import os
import sqlite3
import random
import string
from datetime import date as date_type
from contextlib import contextmanager

DB_PATH = os.environ.get("DB_PATH", "expenses.db")


@contextmanager
def _conn():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def init_db():
    with _conn() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                short_id   TEXT UNIQUE NOT NULL,
                type       TEXT NOT NULL,
                amount     REAL NOT NULL,
                category   TEXT NOT NULL DEFAULT 'general',
                date       TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)


def _make_short_id(con) -> str:
    while True:
        sid = "".join(random.choices(string.ascii_letters + string.digits, k=6))
        row = con.execute("SELECT 1 FROM transactions WHERE short_id = ?", (sid,)).fetchone()
        if not row:
            return sid


def add_transaction(type_: str, amount: float, category: str = "general", date: str = None) -> str:
    if date is None:
        date = date_type.today().isoformat()
    with _conn() as con:
        sid = _make_short_id(con)
        con.execute(
            "INSERT INTO transactions (short_id, type, amount, category, date) VALUES (?, ?, ?, ?, ?)",
            (sid, type_, amount, category, date),
        )
    return sid


def get_transaction(short_id: str):
    with _conn() as con:
        return con.execute(
            "SELECT * FROM transactions WHERE short_id = ?", (short_id,)
        ).fetchone()


def update_transaction(short_id: str, amount: float, type_: str, category: str = None) -> bool:
    with _conn() as con:
        if category is not None:
            con.execute(
                "UPDATE transactions SET amount = ?, type = ?, category = ? WHERE short_id = ?",
                (amount, type_, category, short_id),
            )
        else:
            con.execute(
                "UPDATE transactions SET amount = ?, type = ? WHERE short_id = ?",
                (amount, type_, short_id),
            )
        return con.execute(
            "SELECT changes()"
        ).fetchone()[0] > 0


def delete_transaction(short_id: str) -> bool:
    with _conn() as con:
        con.execute("DELETE FROM transactions WHERE short_id = ?", (short_id,))
        return con.execute("SELECT changes()").fetchone()[0] > 0


def get_all_expenses() -> list:
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM transactions WHERE type = 'expense' ORDER BY date DESC, id DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_current_cycle():
    with _conn() as con:
        last_income = con.execute(
            "SELECT date FROM transactions WHERE type = 'salary' ORDER BY date DESC, id DESC LIMIT 1"
        ).fetchone()

        if last_income:
            start_date = last_income["date"]
            rows = con.execute(
                "SELECT * FROM transactions WHERE date >= ? ORDER BY date ASC, id ASC",
                (start_date,),
            ).fetchall()
        else:
            start_date = None
            rows = con.execute(
                "SELECT * FROM transactions ORDER BY date ASC, id ASC"
            ).fetchall()

    return start_date, [dict(r) for r in rows]
