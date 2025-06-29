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
intents.presences = True # Necessário para o status_changer ver o estado dos membros e para atividades

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

    # Configura base de dados (cria tabelas se não existirem)
    setup_database()
    print('📦 Base de dados configurada.')

    # Carrega cogs
    if not os.path.exists('cogs'):
        print("⚠️ Pasta 'cogs' não encontrada. Certifique-se de que seus cogs estão na subpasta 'cogs'.")
        return

    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and filename not in ['__init__.py', '__pycache__']: # Ignora arquivos de sistema
            try:
                # Carrega a extensão (cog)
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'✅ Cog {filename[:-3]} carregado.')
            except Exception as e:
                print(f'❌ Erro ao carregar cog {filename[:-3]}: {e}')

    print('🚀 Todos os cogs foram carregados.')
    print('------') 

    # Se você planeja usar Slash Commands, descomente a linha abaixo após o bot carregar todos os cogs
    # await bot.tree.sync() # Sincroniza a árvore de comandos de aplicação (slash commands)

# --- Executa o bot ---
if __name__ == '__main__':
    # Certifique-se de que seu DISCORD_BOT_TOKEN está configurado nas variáveis de ambiente
    if TOKEN is None:
        print("ERRO: DISCORD_BOT_TOKEN não encontrado nas variáveis de ambiente.")
        print("Por favor, defina a variável de ambiente DISCORD_BOT_TOKEN com o token do seu bot.")
    else:
        bot.run(TOKEN)
