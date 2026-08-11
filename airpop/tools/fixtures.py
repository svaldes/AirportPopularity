"""Generate fake poll samples into data/sample.db for testing roll-ups."""

import random
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from airpop.collector import POLL_INTERVAL_SEC
from airpop.db import init_db

SAMPLE_DB_PATH = Path("data") / "sample.db"
DEFAULT_DAYS = 14
DEFAULT_START_COUNT = 5
RANDOM_SEED = 0


def fake_count(prev: int) -> int:
    """Random walk: 99% same, 0.5% +1, 0.5% -1 (clamped at 0)."""
    r = random.random()
    if r < 0.005:
        return max(0, prev - 1)
    if r < 0.010:
        return prev + 1
    return prev


def generate_samples(
    n: int,
    *,
    start: datetime,
    interval_sec: int = POLL_INTERVAL_SEC,
    start_count: int = DEFAULT_START_COUNT,
    db_path: Path = SAMPLE_DB_PATH,
) -> None:
    """Write n synthetic rows, spaced interval_sec apart, starting at `start`."""
    init_db(db_path)
    count = start_count
    rows: list[tuple[str, int]] = []
    for i in range(n):
        when = start + timedelta(seconds=i * interval_sec)
        count = fake_count(count)
        rows.append((when.isoformat(), count))
    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            "INSERT INTO poll_samples (polled_at, count) VALUES (?, ?)",
            rows,
        )
        conn.commit()


def main() -> None:
    random.seed(RANDOM_SEED)
    n = DEFAULT_DAYS * 24 * 60 * 60 // POLL_INTERVAL_SEC
    start = datetime.now(timezone.utc) - timedelta(days=DEFAULT_DAYS)
    if SAMPLE_DB_PATH.exists():
        SAMPLE_DB_PATH.unlink()
    print(f"writing {n} samples to {SAMPLE_DB_PATH} ({DEFAULT_DAYS} days @ {POLL_INTERVAL_SEC}s)")
    generate_samples(n, start=start)
    print("done")


if __name__ == "__main__":
    main()
