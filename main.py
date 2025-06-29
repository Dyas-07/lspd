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
intents.presences = True 

# Bot com prefixo "!"
bot = commands.Bot(command_prefix='!', intents=intents)

# --- COMANDO COM PREFIXO (!mascote) ---
@bot.command(name="mascote")
async def hello(ctx):
    if not isinstance(ctx.author, discord.Member):
        await ctx.send("Este comando só pode ser usado num servidor.")
        return

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
                # Carrega a extensão (cog)
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'✅ Cog {filename[:-3]} carregado.')
            except Exception as e:
                print(f'❌ Erro ao carregar cog {filename[:-3]}: {e}')

    print('🚀 Todos os cogs foram carregados.')
    print('------') 

    # Sincroniza a árvore de comandos de aplicação (slash commands) - embora setuppunch seja de prefixo,
    # isto garante que o bot está totalmente inicializado. Pode ser útil para cogs que usam slash commands.
    # Esta linha não é estritamente necessária para comandos de prefixo, mas não faz mal.
    # await bot.tree.sync() # Descomente se estiver a usar ou planeia usar slash commands

# --- Executa o bot ---
if __name__ == '__main__':
    bot.run(TOKEN)
