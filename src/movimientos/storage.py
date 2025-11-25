from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable

from .models import Transaction

DEFAULT_DB_PATH = Path("data/transactions.db")


def ensure_db(db_path: Path = DEFAULT_DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                balance REAL,
                currency TEXT NOT NULL,
                raw_reference TEXT,
                source_file TEXT NOT NULL,
                ingested_at TEXT NOT NULL
            )
            """
        )


def insert_transactions(
    transactions: Iterable[Transaction],
    db_path: Path = DEFAULT_DB_PATH,
) -> int:
    ensure_db(db_path)
    to_insert = [t.as_db_tuple() for t in transactions]
    if not to_insert:
        return 0

    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            """
            INSERT INTO transactions (
                provider, date, description, amount, balance, currency, raw_reference, source_file, ingested_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [item + (datetime.utcnow().isoformat(),) for item in to_insert],
        )
        conn.commit()
    return len(to_insert)


def list_transactions(db_path: Path = DEFAULT_DB_PATH) -> list[dict]:
    ensure_db(db_path)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            "SELECT provider, date, description, amount, balance, currency, raw_reference, source_file, ingested_at FROM transactions ORDER BY date"
        )
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
