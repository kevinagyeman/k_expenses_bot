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
                user_id    INTEGER NOT NULL DEFAULT 0,
                cycle_seq  INTEGER,
                type       TEXT NOT NULL,
                amount     REAL NOT NULL,
                category   TEXT NOT NULL DEFAULT 'general',
                date       TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        for col, definition in [
            ("user_id", "INTEGER NOT NULL DEFAULT 0"),
            ("cycle_seq", "INTEGER"),
        ]:
            try:
                con.execute(f"ALTER TABLE transactions ADD COLUMN {col} {definition}")
            except Exception:
                pass


def _make_short_id(con) -> str:
    while True:
        sid = "".join(random.choices(string.ascii_letters + string.digits, k=6))
        row = con.execute("SELECT 1 FROM transactions WHERE short_id = ?", (sid,)).fetchone()
        if not row:
            return sid


def _next_cycle_seq(con, user_id: int, is_salary: bool) -> int:
    if is_salary:
        return 1
    last_salary = con.execute(
        "SELECT id FROM transactions WHERE type = 'salary' AND user_id = ? ORDER BY id DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    cycle_start_id = last_salary["id"] if last_salary else 0
    row = con.execute(
        "SELECT COALESCE(MAX(cycle_seq), 0) + 1 FROM transactions WHERE user_id = ? AND id >= ?",
        (user_id, cycle_start_id),
    ).fetchone()
    return row[0]


def add_transaction(user_id: int, type_: str, amount: float, category: str = "general", date: str = None) -> tuple[str, int]:
    if date is None:
        date = date_type.today().isoformat()
    with _conn() as con:
        cycle_seq = _next_cycle_seq(con, user_id, type_ == "salary")
        sid = _make_short_id(con)
        con.execute(
            "INSERT INTO transactions (short_id, user_id, cycle_seq, type, amount, category, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (sid, user_id, cycle_seq, type_, amount, category, date),
        )
    return sid, cycle_seq


def get_transaction_by_seq(user_id: int, cycle_seq: int):
    with _conn() as con:
        last_salary = con.execute(
            "SELECT id FROM transactions WHERE type = 'salary' AND user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()
        cycle_start_id = last_salary["id"] if last_salary else 0
        return con.execute(
            "SELECT * FROM transactions WHERE user_id = ? AND cycle_seq = ? AND id >= ?",
            (user_id, cycle_seq, cycle_start_id),
        ).fetchone()


def delete_last_transaction(user_id: int) -> dict | None:
    with _conn() as con:
        row = con.execute(
            "SELECT * FROM transactions WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()
        if not row:
            return None
        con.execute("DELETE FROM transactions WHERE id = ?", (row["id"],))
    return dict(row)


def get_transaction(user_id: int, short_id: str):
    with _conn() as con:
        return con.execute(
            "SELECT * FROM transactions WHERE short_id = ? AND user_id = ?", (short_id, user_id)
        ).fetchone()


def update_transaction(user_id: int, short_id: str, amount: float, type_: str, category: str = None) -> bool:
    with _conn() as con:
        if category is not None:
            con.execute(
                "UPDATE transactions SET amount = ?, type = ?, category = ? WHERE short_id = ? AND user_id = ?",
                (amount, type_, category, short_id, user_id),
            )
        else:
            con.execute(
                "UPDATE transactions SET amount = ?, type = ? WHERE short_id = ? AND user_id = ?",
                (amount, type_, short_id, user_id),
            )
        return con.execute("SELECT changes()").fetchone()[0] > 0


def delete_transaction(user_id: int, short_id: str) -> bool:
    with _conn() as con:
        con.execute("DELETE FROM transactions WHERE short_id = ? AND user_id = ?", (short_id, user_id))
        return con.execute("SELECT changes()").fetchone()[0] > 0


def get_all_cycles(user_id: int) -> list:
    with _conn() as con:
        salaries = [dict(r) for r in con.execute(
            "SELECT date, id FROM transactions WHERE type = 'salary' AND user_id = ? ORDER BY date ASC, id ASC",
            (user_id,),
        ).fetchall()]
        all_rows = [dict(r) for r in con.execute(
            "SELECT * FROM transactions WHERE user_id = ? ORDER BY date ASC, id ASC",
            (user_id,),
        ).fetchall()]

    if not salaries:
        return [{"start_date": None, "end_date": None, "transactions": all_rows}]

    cycles = []
    for i, salary in enumerate(salaries):
        start = salary["date"]
        end = salaries[i + 1]["date"] if i + 1 < len(salaries) else None
        rows = [r for r in all_rows if r["date"] >= start and (end is None or r["date"] < end)]
        cycles.append({"start_date": start, "end_date": end, "transactions": rows})

    return cycles


def get_current_cycle(user_id: int):
    with _conn() as con:
        last_income = con.execute(
            "SELECT date FROM transactions WHERE type = 'salary' AND user_id = ? ORDER BY date DESC, id DESC LIMIT 1",
            (user_id,),
        ).fetchone()

        if last_income:
            start_date = last_income["date"]
            rows = con.execute(
                "SELECT * FROM transactions WHERE date >= ? AND user_id = ? ORDER BY date ASC, id ASC",
                (start_date, user_id),
            ).fetchall()
        else:
            start_date = None
            rows = con.execute(
                "SELECT * FROM transactions WHERE user_id = ? ORDER BY date ASC, id ASC",
                (user_id,),
            ).fetchall()

    return start_date, [dict(r) for r in rows]
