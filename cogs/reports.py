# your_bot_folder/cogs/reports.py
import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta

# Importa funções do nosso módulo database
from database import get_punches_for_period
# Importa configurações do nosso módulo config
from config import WEEKLY_REPORT_CHANNEL_ID

class ReportsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Inicia a tarefa em loop para enviar relatórios semanais quando o cog é carregado.
        self.weekly_report_task.start()

    def cog_unload(self):
        """Garante que a tarefa em loop seja parada quando o cog é descarregado."""
        self.weekly_report_task.cancel()

    @tasks.loop(hours=24 * 7) # Executa a cada 7 dias (uma semana)
    async def weekly_report_task(self):
        """
        Esta tarefa envia um relatório semanal das horas de serviço.
        Ela é configurada para rodar a cada 7 dias.
        """
        await self.bot.wait_until_ready() # Garante que o bot esteja pronto antes de iniciar a tarefa.
        
        # Chama a função principal de geração de relatório com o período padrão da semana passada.
        await self._generate_and_send_report()

    # Função auxiliar para gerar e enviar o relatório, reutilizável por loop e comando
    async def _generate_and_send_report(self, start_date: datetime = None, end_date: datetime = None, ctx: commands.Context = None):
        """
        Gera e envia o relatório de horas de serviço para um período específico.
        Se start_date e end_date não forem fornecidos, usa a semana passada.
        """
        now = datetime.now()

        if start_date is None or end_date is None:
            # Lógica para a semana passada (padrão)
            start_of_period = now - timedelta(days=now.weekday() + 7)
            start_of_period = start_of_period.replace(hour=0, minute=0, second=0, microsecond=0)

            end_of_period = start_of_period + timedelta(days=6, hours=23, minutes=59, seconds=59, microseconds=999999)
        else:
            # Usa as datas fornecidas
            start_of_period = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_period = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            if start_of_period > end_of_period:
                if ctx:
                    await ctx.send("Erro: A data de início não pode ser posterior à data de fim.")
                return

        print(f"Gerando relatório de {start_of_period.strftime('%d/%m/%Y %H:%M')} a {end_of_period.strftime('%d/%m/%Y %H:%M')}")

        records = get_punches_for_period(start_of_period, end_of_period)
        user_total_times = {}

        for record in records:
            user_id = record['user_id']
            username = record['username']
            punch_in_str = record['punch_in_time']
            punch_out_str = record['punch_out_time']

            punch_in = datetime.fromisoformat(punch_in_str)
            punch_out = datetime.fromisoformat(punch_out_str)
            
            duration = punch_out - punch_in
            
            if user_id not in user_total_times:
                user_total_times[user_id] = {'username': username, 'total_duration': timedelta(0)}
            user_total_times[user_id]['total_duration'] += duration

        sorted_users = sorted(user_total_times.values(), key=lambda x: x['total_duration'], reverse=True)

        report_channel = self.bot.get_channel(WEEKLY_REPORT_CHANNEL_ID)
        if not report_channel:
            print(f"Erro: Canal de relatório semanal com ID {WEEKLY_REPORT_CHANNEL_ID} não encontrado.")
            if ctx:
                await ctx.send(f"Erro: O canal de relatório semanal (ID: {WEEKLY_REPORT_CHANNEL_ID}) não foi encontrado. Verifique a configuração.")
            return

        period_desc = f"{start_of_period.strftime('%d/%m/%Y')} - {end_of_period.strftime('%d/%m/%Y')}"
        if not sorted_users:
            await report_channel.send(f"**Relatório de Serviço ({period_desc})**\n\nNenhum registro de serviço encontrado para o período especificado.")
            return

        embed = discord.Embed(
            title=f"📊 Relatório de Horas de Serviço (LSPD)",
            description=f"Período: {period_desc}",
            color=discord.Color.green()
        )

        for i, user_data in enumerate(sorted_users):
            username = user_data['username']
            total_duration = user_data['total_duration']
            
            total_seconds = int(total_duration.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            if i < 20:
                embed.add_field(name=f"{i+1}. {username}", value=f"Tempo Total: {hours}h {minutes}m {seconds}s", inline=False)
            else:
                if i == 20:
                    embed.add_field(name="...", value="E mais usuários...", inline=False)
                break

        embed.set_footer(text="Relatório gerado automaticamente pelo Sistema de Ponto LSPD.")
        
        try:
            await report_channel.send(embed=embed)
            print("Relatório enviado com sucesso.")
        except Exception as e:
            print(f"Erro ao enviar relatório: {e}")

    # --- COMANDO PARA FORÇAR O RELATÓRIO SEMANAL ---
    @commands.command(name="forcereport", help="Força a geração e o envio do relatório de horas de serviço. Use !forcereport [DD-MM-YYYY] [DD-MM-YYYY] para um período específico.")
    @commands.has_permissions(administrator=True)
    async def force_weekly_report(self, ctx, start_date_str: str = None, end_date_str: str = None):
        """
        Comando para acionar manualmente a geração do relatório.
        Pode receber datas opcionais no formato DD-MM-YYYY.
        """
        start_date = None
        end_date = None

        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%d-%m-%Y')
            except ValueError:
                await ctx.send("Formato de data inválido para a data de início. Use DD-MM-YYYY.")
                return
        
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%d-%m-%Y')
            except ValueError:
                await ctx.send("Formato de data inválido para a data de fim. Use DD-MM-YYYY.")
                return
        
        await ctx.send("Gerando e enviando o relatório de horas de serviço...")
        # Chama a função auxiliar que agora aceita as datas
        await self._generate_and_send_report(start_date=start_date, end_date=end_date, ctx=ctx)
        await ctx.send("Relatório enviado (se houver dados).")


async def setup(bot):
    await bot.add_cog(ReportsCog(bot))