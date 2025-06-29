import sqlite3
from datetime import datetime, timedelta

from config import DATABASE_NAME # Importa o nome do banco de dados do config.py

def get_db_connection():
    """Retorna uma conexão com o banco de dados."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row # Permite acessar colunas por nome (como um dicionário)
    return conn

def setup_database():
    """
    Cria as tabelas 'punches' e 'tickets' se elas não existirem.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Tabela para registros de picagem de ponto
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS punches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                punch_in_time TEXT,
                punch_out_time TEXT
            )
        ''')
        # Tabela para registros de tickets
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER NOT NULL UNIQUE,
                creator_id INTEGER NOT NULL,
                creator_name TEXT NOT NULL,
                category TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        conn.commit() # Salva as mudanças no banco de dados.
    print("DEBUG: Tabelas de banco de dados 'punches' e 'tickets' verificadas/criadas.")

# --- Funções para Picagem de Ponto ---

def record_punch_in(user_id: int, username: str) -> bool:
    """
    Registra a entrada em serviço de um usuário.
    Retorna True se a entrada foi registrada, False se o usuário já estava em serviço.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Verifica se o usuário já está em serviço (punch_out_time IS NULL)
        cursor.execute("SELECT id FROM punches WHERE user_id = ? AND punch_out_time IS NULL", (user_id,))
        if cursor.fetchone():
            return False # Usuário já está em serviço

        current_time = datetime.now().isoformat() # Armazena em formato ISO 8601
        cursor.execute("INSERT INTO punches (user_id, username, punch_in_time) VALUES (?, ?, ?)",
                       (user_id, username, current_time))
        conn.commit()
        return True

def record_punch_out(user_id: int) -> tuple[bool, timedelta | None]:
    """
    Registra a saída de serviço de um usuário.
    Retorna (True, timedelta) se a saída foi registrada com a duração,
    (False, None) se o usuário não estava em serviço.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Procura o último registro de entrada sem saída para este usuário.
        cursor.execute("SELECT id, punch_in_time FROM punches WHERE user_id = ? AND punch_out_time IS NULL ORDER BY id DESC LIMIT 1", (user_id,))
        active_punch = cursor.fetchone()

        if active_punch:
            punch_id, punch_in_time_str = active_punch
            punch_in_time = datetime.fromisoformat(punch_in_time_str) # Converte de volta para datetime
            current_time = datetime.now().isoformat()
            time_diff = datetime.now() - punch_in_time
            
            # Atualiza o registro com o horário de saída.
            cursor.execute("UPDATE punches SET punch_out_time = ? WHERE id = ?",
                           (current_time, punch_id))
            conn.commit()
            return True, time_diff
        else:
            return False, None

def get_punches_for_period(start_time: datetime, end_time: datetime):
    """
    Retorna todos os registros de picagem de ponto dentro de um período específico.
    Ajusta a data de fim para incluir o dia inteiro.
    """
    # Garante que a end_time inclua todo o último dia (até o último microssegundo)
    adjusted_end_time = end_time.replace(hour=23, minute=59, second=59, microsecond=999999)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, username, punch_in_time, punch_out_time
            FROM punches
            WHERE punch_in_time BETWEEN ? AND ?  -- Filtra pela hora de entrada
            AND punch_out_time IS NOT NULL       -- Apenas registros completos (com entrada e saída)
            ORDER BY punch_in_time ASC           -- Ordena por hora de entrada
        """, (start_time.isoformat(), adjusted_end_time.isoformat()))
        return cursor.fetchall()

def get_open_punches_for_auto_close():
    """
    Retorna todos os registros de ponto que estão abertos (punch_out_time IS NULL).
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, username, punch_in_time
            FROM punches
            WHERE punch_out_time IS NULL
        """)
        return cursor.fetchall()

def auto_record_punch_out(punch_id: int, auto_punch_out_time: datetime):
    """
    Registra uma saída automática para um registro de ponto específico.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE punches SET punch_out_time = ? WHERE id = ?",
                       (auto_punch_out_time.isoformat(), punch_id))
        conn.commit()

# --- Funções para o banco de dados de tickets (mantidas do contexto anterior) ---

def add_ticket_to_db(channel_id: int, creator_id: int, creator_name: str, category: str):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    created_at = datetime.now().isoformat()
    try:
        c.execute("INSERT INTO tickets (channel_id, creator_id, creator_name, category, created_at) VALUES (?, ?, ?, ?, ?)",
                  (channel_id, creator_id, creator_name, category, created_at))
        conn.commit()
        print(f"DEBUG: Ticket {channel_id} (Criador: {creator_name}, Categoria: {category}) adicionado ao DB.")
        return True
    except sqlite3.IntegrityError:
        print(f"DEBUG: Erro: Ticket para o canal {channel_id} já existe no DB.")
        return False
    finally:
        conn.close()

def remove_ticket_from_db(channel_id: int):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM tickets WHERE channel_id = ?", (channel_id,))
    conn.commit()
    print(f"DEBUG: Ticket para o canal {channel_id} removido do DB.")
    conn.close()

def get_all_open_tickets():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("SELECT channel_id, creator_id, creator_name, category, created_at FROM tickets")
    tickets = c.fetchall()
    conn.close()
    # Retorna uma lista de dicionários para facilitar o acesso
    return [{'channel_id': t[0], 'creator_id': t[1], 'creator_name': t[2], 'category': t[3], 'created_at': t[4]} for t in tickets]
