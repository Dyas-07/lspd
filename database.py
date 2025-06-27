# your_bot_folder/database.py
import sqlite3
from datetime import datetime, timedelta

from config import DATABASE_NAME # Importa o nome do banco de dados do config.py

# Conecta-se ao banco de dados SQLite. Se o arquivo não existir, ele será criado.
# Usa a função `connect` sempre que precisar interagir com o DB para evitar problemas de concorrência.
def get_db_connection():
    """Retorna uma conexão com o banco de dados."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row # Permite acessar colunas por nome
    return conn

def setup_database():
    """
    Cria a tabela 'punches' se ela não existir.
    Esta tabela armazenará os registros de entrada e saída.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS punches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                punch_in_time TEXT,
                punch_out_time TEXT
            )
        ''')
        conn.commit() # Salva as mudanças no banco de dados.

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

        current_time = datetime.now().isoformat()
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
            punch_in_time = datetime.fromisoformat(punch_in_time_str)
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
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, username, punch_in_time, punch_out_time
            FROM punches
            WHERE punch_in_time BETWEEN ? AND ?
            AND punch_out_time IS NOT NULL
        """, (start_time.isoformat(), end_time.isoformat()))
        return cursor.fetchall()