
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

def test_new_user_is_not_verified(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_NAME", str(db_path))

    database.init_db()
    database.save_user(123, "Test", "User")

    assert database.is_user_verified(123) is False


def test_verify_user_saves_phone_number(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_NAME", str(db_path))

    database.init_db()
    database.save_user(123, "Test", "User")

    result = database.verify_user(123, "+77001234567")

    assert result is True
    assert database.is_user_verified(123) is True
    assert database.get_phone_number(123) == "+77001234567"


def test_unknown_user_cannot_be_verified(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_NAME", str(db_path))

    database.init_db()

    assert database.verify_user(999, "+77001234567") is False
    assert database.is_user_verified(999) is False


def test_get_user_by_phone_finds_user(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_NAME", str(db_path))

    database.init_db()
    database.save_user(123, "Test", "User")
    database.verify_user(123, "+77001234567")

    recipient = database.get_user_by_phone("+77001234567")

    assert recipient is not None
    assert recipient[0] == 123
    assert recipient[1] == "Test"
    assert recipient[2] == "User"
    assert recipient[4] == 1

def test_get_user_by_phone_returns_none_for_unknown_number(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_NAME", str(db_path))

    database.init_db()

    recipient = database.get_user_by_phone("+77009999999")

    assert recipient is None


def test_get_user_by_phone_without_plus(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_NAME", str(db_path))

    database.init_db()
    database.save_user(123, "Test", "User")
    database.verify_user(123, "+77001234567")

    recipient = database.get_user_by_phone("77001234567")

    assert recipient is not None
    assert recipient[0] == 123
