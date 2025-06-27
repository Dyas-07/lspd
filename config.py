import discord
import os

# Substitua 'SEU_TOKEN_DO_BOT' pelo token real do seu bot do Discord.
# Mantenha o token em segredo e NUNCA o compartilhe publicamente.
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# ID do canal onde a mensagem de picagem de ponto será afixada.
# Clique com o botão direito no canal no Discord e selecione "Copiar ID".
PUNCH_CHANNEL_ID = 1387870298526978231 # Ex: 123456789012345678

# ID do canal onde a lista semanal de horas será enviada.
WEEKLY_REPORT_CHANNEL_ID = 1387870377144881303 # Ex: 123456789012345679

# Nome do arquivo onde o ID da mensagem de picagem de ponto será salvo.
PUNCH_MESSAGE_FILE = 'punch_message_id.txt'

# ID do canal onde os logs de picagem de ponto serão enviados.
# Clique com o botão direito no canal no Discord e selecione "Copiar ID".
PUNCH_LOGS_CHANNEL_ID = 1387870457268666440 # Ex: 123456789012345680

# Nome do arquivo do banco de dados SQLite
DATABASE_NAME = 'punch_card.db'

ROLE_ID = 1245892923233402881  # Substitui pelo ID do cargo autorizado

# your_bot_folder/config.py




# --- Configurações de Status do Bot ---
# O status inicial do bot ao iniciar (online, idle, dnd, invisible)
DEFAULT_STATUS_TYPE = discord.Status.online

# Lista de atividades que o bot irá alternar (opcional)
# Cada tupla deve conter: (Tipo de Atividade, Mensagem, URL se for STREAMING)
# Tipos: discord.ActivityType.playing, discord.ActivityType.watching,
#        discord.ActivityType.listening, discord.ActivityType.streaming
BOT_ACTIVITIES = [
    (discord.ActivityType.playing, "LSPD - KUMA RP", None),


    # Live 1: Exemplo de canal de Twitch
    (discord.ActivityType.streaming, "Moon Clara", "https://www.twitch.tv/xirilikika"),
    
    # Live 2: Exemplo de outro canal de Twitch ou YouTube
    (discord.ActivityType.streaming, "Sofia Bicho", "https://www.twitch.tv/sofialameiras"),
    
    # Live 3: Exemplo de uma live que não tem URL, ou de um parceiro
    (discord.ActivityType.streaming, "Zuka ZK", "https://m.twitch.tv/hyag0o0"),

    (discord.ActivityType.streaming, "Mika Gomez", "https://www.twitch.tv/laraxcross")
]

# Intervalo em segundos para alternar entre as atividades (se BOT_ACTIVITIES não estiver vazio)
ACTIVITY_CHANGE_INTERVAL_SECONDS = 30 # 30 segundos