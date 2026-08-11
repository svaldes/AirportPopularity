"""SQLite storage for poll samples."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path("data")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS poll_samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    polled_at TEXT NOT NULL,
    count INTEGER NOT NULL
);
"""


def db_path_for(icao: str) -> Path:
    """e.g. KVGT -> data/KVGT.db"""
    return DATA_DIR / f"{icao.upper()}.db"


def init_db(path: Path) -> None:
    """Create data directory and poll_samples table if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(_SCHEMA)
        conn.commit()


def insert_poll_sample(
    count: int,
    *,
    path: Path,
    polled_at: datetime | None = None,
) -> None:
    """Append one poll result row."""
    init_db(path)
    when = polled_at or datetime.now(timezone.utc)
    ts = when.isoformat()
    with sqlite3.connect(path) as conn:
        conn.execute(
            "INSERT INTO poll_samples (polled_at, count) VALUES (?, ?)",
            (ts, count),
        )
        conn.commit()
