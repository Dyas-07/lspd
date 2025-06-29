# your_bot_folder/config.py

import os
import discord

# --- Configurações de Conexão e Banco de Dados ---
TOKEN = os.getenv('DISCORD_BOT_TOKEN') # Já configurado para variável de ambiente

# IDs dos Canais (Lidos de variáveis de ambiente)
# Em seu ambiente local, você pode definir essas variáveis antes de rodar o bot.
# No Railway, você as adicionará na seção de variáveis de ambiente.
PUNCH_CHANNEL_ID = int(os.getenv('PUNCH_CHANNEL_ID')) if os.getenv('PUNCH_CHANNEL_ID') else None
WEEKLY_REPORT_CHANNEL_ID = int(os.getenv('WEEKLY_REPORT_CHANNEL_ID')) if os.getenv('WEEKLY_REPORT_CHANNEL_ID') else None
PUNCH_LOGS_CHANNEL_ID = int(os.getenv('PUNCH_LOGS_CHANNEL_ID')) if os.getenv('PUNCH_LOGS_CHANNEL_ID') else None

# Nome do arquivo onde o ID da mensagem de picagem de ponto será salvo.
# Este arquivo é local ao ambiente e não precisa ser uma variável de ambiente.
PUNCH_MESSAGE_FILE = 'punch_message_id.txt'

# Nome do arquivo do banco de dados SQLite
# Para Railway, é comum que a base de dados seja efêmera ou persistida de outra forma (volumes ou bancos de dados reais).
# Para SQLite, ele será criado no contêiner do Railway.
DATABASE_NAME = 'punch_card.db'

# ID do Cargo Autorizado
ROLE_ID = int(os.getenv('ROLE_ID')) if os.getenv('ROLE_ID') else None




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
    (discord.ActivityType.streaming, "Zuka ZK", "https://www.twitch.tv/hyag0o0"),

    (discord.ActivityType.streaming, "Mika Gomez", "https://www.twitch.tv/laraxcross")
]

# Intervalo em segundos para alternar entre as atividades (se BOT_ACTIVITIES não estiver vazio)
ACTIVITY_CHANGE_INTERVAL_SECONDS = 30 # 30 segundos

# your_bot_folder/config.py
import os
import discord

# ... (suas outras configurações existentes, como TOKEN, PUNCH_CHANNEL_ID, etc.) ...

# --- Configurações do Sistema de Tickets ---

# ID do canal onde a mensagem principal do sistema de tickets será enviada (com o dropdown)
# Crie um canal dedicado para o comando !setup_tickets ou !ticket_panel
TICKET_PANEL_CHANNEL_ID = int(os.getenv('TICKET_PANEL_CHANNEL_ID')) if os.getenv('TICKET_PANEL_CHANNEL_ID') else None

# ID do canal onde os transcritos dos tickets fechados serão enviados
TICKET_TRANSCRIPTS_CHANNEL_ID = int(os.getenv('TICKET_TRANSCRIPTS_CHANNEL_ID')) if os.getenv('TICKET_TRANSCRIPTS_CHANNEL_ID') else None

# ID do cargo que pode fechar tickets (e.g., um cargo de Moderador ou Admin)
# Se você tiver vários cargos, pode adicionar uma lista, mas por simplicidade, um ID por enquanto.
TICKET_MODERATOR_ROLE_ID = int(os.getenv('TICKET_MODERATOR_ROLE_ID')) if os.getenv('TICKET_MODERATOR_ROLE_ID') else None

# Nome do arquivo onde o ID da mensagem do painel de tickets será salvo (para persistência)
TICKET_PANEL_MESSAGE_FILE = 'ticket_panel_message_id.txt'

# Categorias de tickets para o dropdown:
# Cada tupla: (label no dropdown, descrição no dropdown, emoji, ID da categoria onde o ticket será criado)
# Os IDs das categorias devem ser obtidos do seu servidor Discord.
TICKET_CATEGORIES = [
    ("Reportar Jogador", "Use para relatar violações de regras de jogadores.", "🚨", int(os.getenv('TICKET_CATEGORY_PLAYER_REPORT_ID')) if os.getenv('TICKET_CATEGORY_PLAYER_REPORT_ID') else None),
    ("Suporte Geral", "Para dúvidas e assistência geral.", "❓", int(os.getenv('TICKET_CATEGORY_GENERAL_SUPPORT_ID')) if os.getenv('TICKET_CATEGORY_GENERAL_SUPPORT_ID') else None),
    ("Recursos Humanos", "Assuntos de RH, candidaturas, etc.", "👔", int(os.getenv('TICKET_CATEGORY_HR_ID')) if os.getenv('TICKET_CATEGORY_HR_ID') else None),
    # Adicione mais categorias conforme necessário
]
