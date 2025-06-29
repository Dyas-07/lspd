import discord
from discord.ext import commands, tasks # Importa tasks para loops assíncronos
from datetime import datetime, timedelta
import asyncio
import os

# Importa funções do nosso módulo database
from database import record_punch_in, record_punch_out, get_open_punches_for_auto_close, auto_record_punch_out, get_punches_for_period
# Importa configurações do nosso módulo config
from config import PUNCH_CHANNEL_ID, PUNCH_MESSAGE_FILE, PUNCH_LOGS_CHANNEL_ID, ROLE_ID # Garante ROLE_ID também para permissões de relatório

# Tempo limite para fechamento automático de ponto (em horas)
AUTO_CLOSE_PUNCH_THRESHOLD_HOURS = 3
# Intervalo em que o bot verifica pontos abertos (em minutos)
AUTO_CLOSE_CHECK_INTERVAL_MINUTES = 5

# --- Classe View para os Botões de Picagem de Ponto ---
class PunchCardView(discord.ui.View):
    def __init__(self, cog_instance):
        super().__init__(timeout=None) # timeout=None faz com que a view persista indefinidamente
        self.cog = cog_instance # Referência para a instância do cog para acessar métodos

    @discord.ui.button(label="Entrar em Serviço", style=discord.ButtonStyle.success, emoji="🟢", custom_id="punch_in_button")
    async def punch_in_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Callback para o botão 'Entrar em Serviço'.
        """
        member = interaction.user
        current_time_str = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        success = record_punch_in(member.id, member.display_name)
        if success:
            await interaction.response.send_message(f"Você entrou em serviço em: {current_time_str}", ephemeral=True)
            print(f'{member.display_name} ({member.id}) entrou em serviço.')

            logs_channel = self.cog.bot.get_channel(PUNCH_LOGS_CHANNEL_ID)
            if logs_channel:
                log_message = f"🟢 **{member.display_name}** (`{member.id}`) entrou em serviço em: `{current_time_str}`."
                await logs_channel.send(log_message)
            else:
                print(f"Erro: Canal de logs com ID {PUNCH_LOGS_CHANNEL_ID} não encontrado.")
        else:
            await interaction.response.send_message("Você já está em serviço! Utilize o botão de 'Sair' para registrar sua saída.", ephemeral=True)

    @discord.ui.button(label="Sair de Serviço", style=discord.ButtonStyle.danger, emoji="🔴", custom_id="punch_out_button")
    async def punch_out_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Callback para o botão 'Sair de Serviço'.
        """
        member = interaction.user
        current_time_str = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        success, time_diff = record_punch_out(member.id)
        if success:
            total_seconds = int(time_diff.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            formatted_time_diff = f"{hours}h {minutes}m {seconds}s"
            
            await interaction.response.send_message(f"Você saiu de serviço em: {current_time_str}. Tempo em serviço: {formatted_time_diff}", ephemeral=True)
            print(f'{member.display_name} ({member.id}) saiu de serviço. Tempo: {time_diff}')

            logs_channel = self.cog.bot.get_channel(PUNCH_LOGS_CHANNEL_ID)
            if logs_channel:
                log_message = f"🔴 **{member.display_name}** (`{member.id}`) saiu de serviço em: `{current_time_str}`. Tempo total: `{formatted_time_diff}`."
                await logs_channel.send(log_message)
            else:
                print(f"Erro: Canal de logs com ID {PUNCH_LOGS_CHANNEL_ID} não encontrado.")
        else:
            await interaction.response.send_message("Você não está em serviço! Utilize o botão de 'Entrar' para registrar sua entrada.", ephemeral=True)

# --- Cog Principal de Picagem de Ponto ---
class PunchCardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._punch_message_id = None
        # O _load_punch_message_id será chamado em on_ready

    async def _load_punch_message_id(self):
        """Carrega o ID da mensagem de picagem de ponto de um arquivo."""
        try:
            with open(PUNCH_MESSAGE_FILE, 'r') as f:
                self._punch_message_id = int(f.read().strip())
        except (FileNotFoundError, ValueError):
            self._punch_message_id = None
        print(f"ID da mensagem de ponto carregado: {self._punch_message_id}")

    async def _save_punch_message_id(self, message_id: int):
        """Salva o ID da mensagem de picagem de ponto em um arquivo."""
        self._punch_message_id = message_id
        with open(PUNCH_MESSAGE_FILE, 'w') as f:
            f.write(str(message_id))
        print(f"ID da mensagem de ponto salvo: {self._punch_message_id}")

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Quando o bot reconecta, adicionamos a View persistente e iniciamos a tarefa de fechamento automático.
        """
        print("PunchCardCog está pronto.")
        await self._load_punch_message_id() # Carrega o ID da mensagem de ponto

        if self._punch_message_id:
            # Tenta buscar a mensagem para garantir que existe antes de adicionar a view
            try:
                channel = self.bot.get_channel(PUNCH_CHANNEL_ID)
                if channel:
                    await channel.fetch_message(self._punch_message_id)
                    self.bot.add_view(PunchCardView(self))
                    print(f"View de picagem de ponto persistente adicionada para a mensagem ID: {self._punch_message_id}")
                else:
                    print(f"Aviso: Canal de picagem de ponto (ID: {PUNCH_CHANNEL_ID}) não encontrado para re-associar a View.")
                    self._punch_message_id = None # Reseta para enviar nova mensagem
            except discord.NotFound:
                print(f"Aviso: Mensagem de picagem de ponto (ID: {self._punch_message_id}) não encontrada, será recriada no próximo setup.")
                self._punch_message_id = None # Reseta para enviar nova mensagem
            except Exception as e:
                print(f"Erro ao re-associar a View de picagem de ponto: {e}")
                self._punch_message_id = None # Reseta em caso de outros erros

        # Inicia a tarefa de fechamento automático de ponto
        self.auto_close_punches.start()
        print("Tarefa de fechamento automático de ponto iniciada.")

    # --- Tarefa de Fechamento Automático de Ponto ---
    @tasks.loop(minutes=AUTO_CLOSE_CHECK_INTERVAL_MINUTES)
    async def auto_close_punches(self):
        """
        Verifica periodicamente por pontos abertos que excederam o limite de tempo
        e os fecha automaticamente.
        """
        # print(f"Verificando pontos abertos para fechamento automático... ({datetime.now().strftime('%H:%M:%S')})") # Descomente para debug
        open_punches = get_open_punches_for_auto_close()
        current_time = datetime.now()
        
        for punch in open_punches:
            punch_id = punch['id']
            user_id = punch['user_id']
            username = punch['username']
            punch_in_time_str = punch['punch_in_time']
            punch_in_time = datetime.fromisoformat(punch_in_time_str)

            time_elapsed = current_time - punch_in_time
            
            # Converte o limite de horas para timedelta
            threshold = timedelta(hours=AUTO_CLOSE_PUNCH_THRESHOLD_HOURS)

            if time_elapsed >= threshold:
                auto_punch_out_time = current_time
                auto_record_punch_out(punch_id, auto_punch_out_time)

                total_seconds = int(time_elapsed.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                formatted_time_elapsed = f"{hours}h {minutes}m {seconds}s"
                
                logs_channel = self.bot.get_channel(PUNCH_LOGS_CHANNEL_ID)
                if logs_channel:
                    log_message = (
                        f"🟡 **{username}** (`{user_id}`) teve o ponto fechado automaticamente "
                        f"por estar aberto por mais de {AUTO_CLOSE_PUNCH_THRESHOLD_HOURS} horas.\n"
                        f"Entrada: `{punch_in_time.strftime('%d/%m/%Y %H:%M:%S')}` | Saída Automática: `{auto_punch_out_time.strftime('%d/%m/%Y %H:%M:%S')}` | Duração: `{formatted_time_elapsed}`."
                    )
                    await logs_channel.send(log_message)
                    print(f"Ponto de {username} (ID: {user_id}) fechado automaticamente.")
                else:
                    print(f"Erro: Canal de logs com ID {PUNCH_LOGS_CHANNEL_ID} não encontrado para registrar fechamento automático.")
            
    @auto_close_punches.before_loop
    async def before_auto_close_punches(self):
        await self.bot.wait_until_ready() # Espera o bot estar pronto antes de iniciar o loop

    # --- Comandos Administrativos ---

    @commands.command(name="setuppunch", help="Envia a mensagem de picagem de ponto para o canal configurado.")
    @commands.has_permissions(administrator=True)
    async def setup_punch_message(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True) # Defer para que o bot "pense"

        channel = self.bot.get_channel(PUNCH_CHANNEL_ID)
        if not channel:
            await ctx.send(f"Erro: Canal de picagem de ponto com ID {PUNCH_CHANNEL_ID} não encontrado.", ephemeral=True)
            return

        embed = discord.Embed(
            title="🕒 Sistema de Picagem de Ponto LSPD",
            description="Utiliza os botões abaixo para registar o início ou o fim do teu serviço.",
            color=discord.Color.blue()
        )
        embed.add_field(name="", value="", inline=False)
        embed.add_field(name="", value="Este sistema garante a organização e monitorização dos horários da LSPD.", inline=False)
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1260308350776774817/1386713008256061512/Untitled_1024_x_1024_px_4.png?ex=685ea921&is=685d57a1&hm=7eade913ed0c813e52280d124181662f80d5ed179fe70b4014b2f61f7192c465&")
        embed.set_footer(
            text="Developed by Dyas",
            icon_url="https://cdn.discordapp.com/attachments/1387870298526978231/1387874932561547437/IMG_6522.jpg?ex=685eeec1&is=685d9d41&hm=0b2e06ee67f221933ead2cbabddef30e04fe115080b9d168dc4d791877d9d9d1&",
        )

        view = PunchCardView(self)

        try:
            if self._punch_message_id:
                message = await channel.fetch_message(self._punch_message_id)
                await message.edit(embed=embed, view=view)
                await ctx.send("Mensagem de picagem de ponto atualizada com sucesso!", ephemeral=True)
            else:
                message = await channel.send(embed=embed, view=view)
                await self._save_punch_message_id(message.id)
                await ctx.send("Mensagem de picagem de ponto enviada com sucesso!", ephemeral=True)
        except discord.NotFound:
            print("Mensagem de picagem de ponto não encontrada, recriando...")
            message = await channel.send(embed=embed, view=view)
            await self._save_punch_message_id(message.id)
            await ctx.send("Mensagem de picagem de ponto recriada com sucesso!", ephemeral=True)
        except Exception as e:
            await ctx.send(f"Erro ao enviar/atualizar mensagem de picagem de ponto: {e}", ephemeral=True)
            print(f"Erro ao enviar/atualizar mensagem de picagem de ponto: {e}")

    @commands.command(name="relatorio", help="Gera um relatório de horas de serviço por período. Ex: !relatorio 01/01/2025 31/01/2025")
    @commands.has_role(ROLE_ID) # Assumindo que ROLE_ID é o cargo autorizado para relatórios
    async def generate_report(self, ctx: commands.Context, start_date_str: str, end_date_str: str):
        await ctx.defer(ephemeral=True)

        try:
            # Converte as strings de data para objetos datetime
            start_date = datetime.strptime(start_date_str, '%d/%m/%Y')
            end_date = datetime.strptime(end_date_str, '%d/%m/%Y')
            
            # A função get_punches_for_period no database.py já ajusta end_date para 23:59:59.
            punches = get_punches_for_period(start_date, end_date)

            if not punches:
                await ctx.send("Nenhum registro de ponto encontrado para o período especificado.", ephemeral=True)
                return

            # Agrupa os dados por utilizador e calcula o tempo total
            user_total_times = {}
            for punch in punches:
                user_id = punch['user_id']
                username = punch['username']
                punch_in_time = datetime.fromisoformat(punch['punch_in_time'])
                punch_out_time = datetime.fromisoformat(punch['punch_out_time'])

                duration = punch_out_time - punch_in_time
                user_total_times.setdefault(user_id, {'username': username, 'total_duration': timedelta(0)})
                user_total_times[user_id]['total_duration'] += duration

            # --- CONSTRUÇÃO DA EMBED DO RELATÓRIO ---
            embed = discord.Embed(
                title="📊 Relatório de Horas de Serviço (LSPD)",
                description=f"**Período:** `{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}`",
                color=discord.Color.from_rgb(50, 205, 50) # Verde vibrante
            )
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1260308350776774817/1386713008256061512/Untitled_1024_x_1024_px_4.png") # Logo LSPD
            
            # Ordena os utilizadores pelo tempo total em serviço (do maior para o menor)
            sorted_users = sorted(user_total_times.items(), key=lambda item: item[1]['total_duration'], reverse=True)

            # Adiciona os membros como campos da embed
            if sorted_users:
                # Cada campo tem um limite de 1024 caracteres. Vamos criar múltiplos campos se necessário.
                current_field_value = ""
                field_count = 0
                
                for i, (user_id, data) in enumerate(sorted_users):
                    username = data['username']
                    total_duration = data['total_duration']
                    
                    total_seconds = int(total_duration.total_seconds())
                    hours, remainder = divmod(total_seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    formatted_total_time = f"{hours}h {minutes}m {seconds}s"
                    
                    # Linha para o relatório
                    line = f"**{i+1}. {username}** (`{user_id}`)\nTempo Total: `{formatted_total_time}`"
                    
                    if len(current_field_value) + len(line) + 1 > 1024 and current_field_value: # +1 para o '\n'
                        embed.add_field(name=f"Membros em Serviço (parte {field_count + 1})", value=current_field_value, inline=False)
                        current_field_value = line
                        field_count += 1
                    else:
                        if current_field_value:
                            current_field_value += "\n" + line
                        else:
                            current_field_value = line
                
                # Adiciona o último campo (se não estiver vazio)
                if current_field_value:
                    if field_count == 0: # Se tudo coube em um campo
                         embed.add_field(name="Membros em Serviço", value=current_field_value, inline=False)
                    else: # Se foram criados múltiplos campos
                         embed.add_field(name=f"Membros em Serviço (parte {field_count + 1})", value=current_field_value, inline=False)

            embed.set_footer(
                text="Relatório gerado automaticamente pelo Sistema de Ponto LSPD.",
                icon_url="https://cdn.discordapp.com/attachments/1387870298526978231/1387874932561547437/IMG_6522.jpg" # Logo "Developed by Dyas"
            )
            # --- FIM DA CONSTRUÇÃO DA EMBED ---

            await ctx.send(embed=embed, ephemeral=True)

        except ValueError:
            await ctx.send("Formato de data inválido. Use DD/MM/YYYY. Ex: `!relatorio 01/01/2025 31/01/2025`", ephemeral=True)
        except Exception as e:
            await ctx.send(f"Ocorreu um erro ao gerar o relatório: `{e}`", ephemeral=True)
            print(f"Erro ao gerar relatório de ponto: {e}")


async def setup(bot):
    """
    Função necessária para que o Discord.py possa carregar este cog.
    """
    await bot.add_cog(PunchCardCog(bot))
