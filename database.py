
import sqlite3

DB_NAME = "bot.db"


def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL
            )
        """)


def get_user(telegram_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.execute(
            """
            SELECT first_name, last_name
            FROM users
            WHERE telegram_id = ?
            """,
            (telegram_id,)
        )
        return cursor.fetchone()


def save_user(telegram_id, first_name, last_name):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            """
            INSERT INTO users (telegram_id, first_name, last_name)
            VALUES (?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                first_name = excluded.first_name,
                last_name = excluded.last_name
            """,
            (telegram_id, first_name, last_name)
        )
