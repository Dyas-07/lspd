# your_bot_folder/main.py
import discord
from discord.ext import commands
import os
import asyncio

# Importa configurações
from config import TOKEN, PUNCH_CHANNEL_ID, WEEKLY_REPORT_CHANNEL_ID, ROLE_ID

# Setup da base de dados
from database import setup_database

# Intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True
intents.presences = True # Adicione esta intent se for usar o status_changer de forma mais robusta

# Bot com prefixo "!"
bot = commands.Bot(command_prefix='!', intents=intents)

# --- COMANDO COM PREFIXO (!mascote) ---
@bot.command(name="mascote")
async def hello(ctx):
    if not isinstance(ctx.author, discord.Member):
        await ctx.send("Este comando só pode ser usado num servidor.")
        return

    # Certifique-se que ROLE_ID está correto em config.py
    # Ou use @commands.has_role(ROLE_ID) como decorador se preferir
    role = discord.utils.get(ctx.author.roles, id=ROLE_ID)

    if role is None:
        await ctx.send("🚫 Não tens permissões para isso.")
    else:
        await ctx.send("A atual mascote da LSPD é o SKIBIDI ZEKA!")

# --- Evento on_ready ---
@bot.event
async def on_ready():
    print(f'✅ Bot conectado como {bot.user.name} ({bot.user.id})')

    # Configura base de dados
    setup_database()
    print('📦 Base de dados configurada.')

    # Carrega cogs
    if not os.path.exists('cogs'):
        print("⚠️ Pasta 'cogs' não encontrada.")
        return

    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'✅ Cog {filename[:-3]} carregado.')
            except Exception as e:
                print(f'❌ Erro ao carregar cog {filename[:-3]}: {e}')

    print('🚀 Todos os cogs foram carregados.')

    # REMOVIDO: A chamada para send_or_update_punch_message()
    # A lógica para re-associar a view de ponto está agora no on_ready do PunchCardCog
    # E a criação inicial/atualização é feita pelo comando !setuppunch

    print('------') # Linha divisória para melhor legibilidade no log
    # A tarefa de mudança de atividade do status_changer cog (se estiver a usar)
    # será iniciada no on_ready desse cog.

# --- Executa o bot ---
if __name__ == '__main__':
    bot.run(TOKEN)
