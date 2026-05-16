import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional
from utils.config import DB_PATH
from utils.logger import logger


class Memory:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        self._init_db()

    def _init_db(self):
        db_file = Path(self.db_path)
        if db_file.is_absolute():
            db_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            Path("./").mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()
        logger.info(f"Base de datos inicializada: {self.db_path}")

    def save_fact(self, key: str, value: str) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO facts (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
            """, (key, value))
            conn.commit()
            conn.close()
            logger.agent_action("SAVE_FACT", f"key={key}")
            return True
        except Exception as e:
            logger.error(f"Error guardando hecho: {e}")
            return False

    def get_fact(self, key: str) -> Optional[str]:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM facts WHERE key = ?", (key,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Error obteniendo hecho: {e}")
            return None

    def get_all_facts(self) -> dict:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM facts")
            result = {row[0]: row[1] for row in cursor.fetchall()}
            conn.close()
            return result
        except Exception as e:
            logger.error(f"Error obteniendo todos los hechos: {e}")
            return {}

    def add_message(self, role: str, content: str) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO conversations (role, content) VALUES (?, ?)", (role, content))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error agregando mensaje: {e}")
            return False

    def get_conversation_history(self, limit: int = 20) -> list:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT role, content FROM conversations
                ORDER BY id ASC LIMIT ?
            """, (limit,))
            result = [{"role": row[0], "content": row[1]} for row in cursor.fetchall()]
            conn.close()
            return result
        except Exception as e:
            logger.error(f"Error obteniendo historial: {e}")
            return []

    def clear_conversation(self) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM conversations")
            conn.commit()
            conn.close()
            logger.agent_action("CLEAR_CONVERSATION", "Historial limpiado")
            return True
        except Exception as e:
            logger.error(f"Error limpiando conversación: {e}")
            return False

    def log_action(self, action: str, details: str = ""):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO session_logs (action, details) VALUES (?, ?)", (action, details))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error en log de sesión: {e}")