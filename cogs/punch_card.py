# your_bot_folder/cogs/punch_card.py
import discord
from discord.ext import commands
from datetime import datetime
import asyncio
import os

# Importa funções do nosso módulo database
from database import record_punch_in, record_punch_out
# Importa configurações do nosso módulo config
# Adicione PUNCH_LOGS_CHANNEL_ID aqui
from config import PUNCH_CHANNEL_ID, PUNCH_MESSAGE_FILE, PUNCH_LOGS_CHANNEL_ID

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

            # --- NOVO: Enviar para o canal de logs ---
            logs_channel = self.cog.bot.get_channel(PUNCH_LOGS_CHANNEL_ID)
            if logs_channel:
                log_message = f"🟢 **{member.display_name}** (`{member.id}`) entrou em serviço em: `{current_time_str}`."
                await logs_channel.send(log_message)
            else:
                print(f"Erro: Canal de logs com ID {PUNCH_LOGS_CHANNEL_ID} não encontrado.")
            # --- FIM NOVO ---

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

            # --- NOVO: Enviar para o canal de logs ---
            logs_channel = self.cog.bot.get_channel(PUNCH_LOGS_CHANNEL_ID)
            if logs_channel:
                log_message = f"🔴 **{member.display_name}** (`{member.id}`) saiu de serviço em: `{current_time_str}`. Tempo total: `{formatted_time_diff}`."
                await logs_channel.send(log_message)
            else:
                print(f"Erro: Canal de logs com ID {PUNCH_LOGS_CHANNEL_ID} não encontrado.")
            # --- FIM NOVO ---

        else:
            await interaction.response.send_message("Você não está em serviço! Utilize o botão de 'Entrar' para registrar sua entrada.", ephemeral=True)

# --- Cog Principal de Picagem de Ponto ---
class PunchCardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._punch_message_id = None
        # Carrega o ID da mensagem de ponto quando o cog é inicializado
        asyncio.create_task(self._load_punch_message_id())

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
        Quando o bot reconecta, adicionamos a View persistente.
        Isso é crucial para que os botões funcionem após reinícios do bot.
        """
        if self._punch_message_id:
            # Adiciona a view persistente ao bot.
            # O bot irá automaticamente reassociar os botões com os callbacks.
            self.bot.add_view(PunchCardView(self))
            print(f"View de picagem de ponto persistente adicionada para a mensagem ID: {self._punch_message_id}")

    async def send_or_update_punch_message(self):
        """
        Envia a mensagem de picagem de ponto ou atualiza uma existente.
        Esta função é chamada uma vez na inicialização do bot (no main.py).
        """
        channel = self.bot.get_channel(PUNCH_CHANNEL_ID)
        if not channel:
            print(f"Erro: Canal de picagem de ponto com ID {PUNCH_CHANNEL_ID} não encontrado.")
            return

        embed = discord.Embed(
            title="🕒  Sistema de Picagem de Ponto LSPD",
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

        # Cria uma instância da View com os botões
        view = PunchCardView(self)

        try:
            if self._punch_message_id:
                # Tenta buscar a mensagem existente.
                message = await channel.fetch_message(self._punch_message_id)
                await message.edit(embed=embed, view=view) # Atualiza a embed e a view
                print(f"Mensagem de picagem de ponto atualizada no canal {channel.name}.")
            else:
                # Se não houver ID salvo, envia uma nova mensagem.
                message = await channel.send(embed=embed, view=view) # Envia a embed com a view
                await self._save_punch_message_id(message.id)
                print(f"Mensagem de picagem de ponto enviada no canal {channel.name}.")
        except discord.NotFound:
            # A mensagem não existe mais (foi deletada), envia uma nova.
            print("Mensagem de picagem de ponto não encontrada, recriando...")
            message = await channel.send(embed=embed, view=view) # Recria a embed com a view
            await self._save_punch_message_id(message.id)
            print(f"Mensagem de picagem de ponto recriada no canal {channel.name}.")
        except Exception as e:
            print(f"Erro ao enviar/atualizar mensagem de picagem de ponto: {e}")


async def setup(bot):
    """
    Função necessária para que o Discord.py possa carregar este cog.
    """
    await bot.add_cog(PunchCardCog(bot))