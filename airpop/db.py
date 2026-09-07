"""SQLite storage for poll samples."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path("data")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS poll_samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    polled_at TEXT NOT NULL,
    in_air INTEGER NOT NULL,
    on_ground INTEGER NOT NULL
);
"""


def db_path_for(icao: str) -> Path:
    """e.g. KVGT -> data/KVGT.db"""
    return DATA_DIR / f"{icao.upper()}.db"


def _column_names(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Create poll_samples if needed, then walk old shapes forward.

    Disposable: once every live DB is on (in_air, on_ground), this can
    collapse to CREATE TABLE IF NOT EXISTS only.

    Handles:
    - brand-new file
    - legacy (polled_at, count)
    - brief (polled_at, count, on_ground)
    - current (polled_at, in_air, on_ground)
    """
    conn.execute(_SCHEMA)
    cols = _column_names(conn, "poll_samples")
    if not cols:
        raise RuntimeError("poll_samples table missing after CREATE")

    if "on_ground" not in cols:
        conn.execute("ALTER TABLE poll_samples ADD COLUMN on_ground INTEGER")
        cols.add("on_ground")

    if "in_air" not in cols:
        if "count" not in cols:
            raise RuntimeError(
                f"poll_samples has neither in_air nor count; columns={sorted(cols)}"
            )
        conn.execute("ALTER TABLE poll_samples RENAME COLUMN count TO in_air")
        cols.discard("count")
        cols.add("in_air")


def init_db(path: Path) -> None:
    """Create data directory and bring poll_samples up to the current schema."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        ensure_schema(conn)
        conn.commit()


def insert_poll_sample(
    in_air: int,
    *,
    path: Path,
    on_ground: int = 0,
    polled_at: datetime | None = None,
) -> None:
    """Append one poll result row (in-air count + on-ground count)."""
    init_db(path)
    when = polled_at or datetime.now(timezone.utc)
    ts = when.isoformat()
    with sqlite3.connect(path) as conn:
        conn.execute(
            "INSERT INTO poll_samples (polled_at, in_air, on_ground) VALUES (?, ?, ?)",
            (ts, in_air, on_ground),
        )
        conn.commit()
