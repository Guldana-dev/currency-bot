
import sqlite3

import database


def test_new_user_gets_1000_balance(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_NAME", str(db_path))

    database.init_db()
    database.save_user(123, "Test", "User")

    assert database.get_balance(123) == 1000


def test_existing_user_balance_is_not_reset(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_NAME", str(db_path))

    database.init_db()
    database.save_user(123, "Test", "User")

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE users SET balance = 500 WHERE telegram_id = 123"
        )

    database.save_user(123, "Updated", "User")

    assert database.get_balance(123) == 500


def test_get_balance_returns_none_for_unknown_user(
    tmp_path, monkeypatch
):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_NAME", str(db_path))

    database.init_db()

    assert database.get_balance(999) is None


def test_old_database_gets_balance_column(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_NAME", str(db_path))

    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE users (
                telegram_id INTEGER PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL
            )
        """)
        conn.execute("""
            INSERT INTO users (telegram_id, first_name, last_name)
            VALUES (123, 'Old', 'User')
        """)

    database.init_db()

    assert database.get_balance(123) == 1000
