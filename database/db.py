import sqlite3
import os
from datetime import date, timedelta

from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "spendly.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL,
            email         TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            created_at    TEXT    DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            amount      REAL    NOT NULL,
            category    TEXT    NOT NULL,
            date        TEXT    NOT NULL,
            description TEXT,
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


def seed_db():
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if count > 0:
        conn.close()
        return

    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
    )
    user_id = conn.execute("SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)).fetchone()[0]

    today = date.today()
    first_of_month = today.replace(day=1)
    expenses = [
        (user_id, 45.50,  "Food",          (first_of_month + timedelta(days=0)).isoformat(), "Groceries"),
        (user_id, 12.00,  "Transport",     (first_of_month + timedelta(days=3)).isoformat(), "Bus pass top-up"),
        (user_id, 85.00,  "Bills",         (first_of_month + timedelta(days=5)).isoformat(), "Electricity bill"),
        (user_id, 30.00,  "Health",        (first_of_month + timedelta(days=8)).isoformat(), "Pharmacy"),
        (user_id, 15.99,  "Entertainment", (first_of_month + timedelta(days=11)).isoformat(), "Movie ticket"),
        (user_id, 62.75,  "Shopping",      (first_of_month + timedelta(days=14)).isoformat(), "New headphones"),
        (user_id, 20.00,  "Other",         (first_of_month + timedelta(days=17)).isoformat(), "Gift for a friend"),
        (user_id, 38.25,  "Food",          (first_of_month + timedelta(days=20)).isoformat(), "Restaurant dinner"),
    ]
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        expenses,
    )
    conn.commit()
    conn.close()
