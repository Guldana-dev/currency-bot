
import sqlite3

DB_NAME = "bot.db"


def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                balance INTEGER NOT NULL DEFAULT 1000,
                phone_number TEXT,
                is_verified INTEGER NOT NULL DEFAULT 0
            )
        """)

        # Проверяем существующие колонки
        columns = conn.execute(
            "PRAGMA table_info(users)"
        ).fetchall()

        column_names = [column[1] for column in columns]

        # Добавляем баланс в старую базу
        if "balance" not in column_names:
            conn.execute("""
                ALTER TABLE users
                ADD COLUMN balance INTEGER NOT NULL DEFAULT 1000
            """)

        # Добавляем номер телефона
        if "phone_number" not in column_names:
            conn.execute("""
                ALTER TABLE users
                ADD COLUMN phone_number TEXT
            """)

        # Добавляем статус верификации
        if "is_verified" not in column_names:
            conn.execute("""
                ALTER TABLE users
                ADD COLUMN is_verified INTEGER NOT NULL DEFAULT 0
            """)
        # Создаём таблицу истории переводов
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                amount INTEGER NOT NULL CHECK(amount > 0),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
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
            INSERT INTO users (
                telegram_id, first_name, last_name, balance
            )
            VALUES (?, ?, ?, 1000)
            ON CONFLICT(telegram_id) DO UPDATE SET
                first_name = excluded.first_name,
                last_name = excluded.last_name
            """,
            (telegram_id, first_name, last_name)
        )


def get_balance(telegram_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.execute(
            """
            SELECT balance
            FROM users
            WHERE telegram_id = ?
            """,
            (telegram_id,)
        )
        result = cursor.fetchone()

        if result:
            return result[0]

        return None


def verify_user(telegram_id, phone_number):
    phone_number = phone_number.strip()

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.execute(
            """
            UPDATE users
            SET phone_number = ?, is_verified = 1
            WHERE telegram_id = ?
            AND first_name != ''
            AND last_name != ''
            """,
            (phone_number, telegram_id)
        )

        return cursor.rowcount == 1


def is_user_verified(telegram_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.execute(
            """
            SELECT is_verified
            FROM users
            WHERE telegram_id = ?
            """,
            (telegram_id,)
        )

        result = cursor.fetchone()

        return bool(result[0]) if result else False


def get_phone_number(telegram_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.execute(
            """
            SELECT phone_number
            FROM users
            WHERE telegram_id = ?
            """,
            (telegram_id,)
        )

        result = cursor.fetchone()

        return result[0] if result else None
def get_user_by_id(telegram_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.execute(
            """
            SELECT telegram_id, first_name, last_name,
                   balance, is_verified
            FROM users
            WHERE telegram_id = ?
            """,
            (telegram_id,)
        )

        return cursor.fetchone()
    

def transfer_money(sender_id, receiver_id, amount):
    if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
        return False, "Сумма должна быть положительным целым числом"

    if sender_id == receiver_id:
        return False, "Нельзя переводить деньги самому себе"

    conn = sqlite3.connect(DB_NAME)

    try:
        with conn:
            conn.execute("BEGIN IMMEDIATE")

            sender = conn.execute(
                """
                SELECT balance, is_verified
                FROM users
                WHERE telegram_id = ?
                """,
                (sender_id,)
            ).fetchone()

            receiver = conn.execute(
                """
                SELECT balance, is_verified
                FROM users
                WHERE telegram_id = ?
                """,
                (receiver_id,)
            ).fetchone()

            if sender is None or receiver is None:
                return False, "Отправитель или получатель не найден"

            if not sender[1] or not receiver[1]:
                return False, "Оба пользователя должны пройти верификацию"

            if sender[0] < amount:
                return False, "Недостаточно средств"

            conn.execute(
                """
                UPDATE users
                SET balance = balance - ?
                WHERE telegram_id = ?
                """,
                (amount, sender_id)
            )

            conn.execute(
                """
                UPDATE users
                SET balance = balance + ?
                WHERE telegram_id = ?
                """,
                (amount, receiver_id)
            )

            conn.execute(
                """
                INSERT INTO transfers (sender_id, receiver_id, amount)
                VALUES (?, ?, ?)
                """,
                (sender_id, receiver_id, amount)
            )

        return True, "Перевод успешно выполнен"

    finally:
        conn.close()
        
def get_user_by_phone(phone_number):
    phone_number = phone_number.strip()

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.execute(
            """
            SELECT telegram_id, first_name, last_name,
                   balance, is_verified
            FROM users
            WHERE phone_number = ?
            """,
            (phone_number,)
        )

        return cursor.fetchone()
