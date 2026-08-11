"""Build a static Chart.js page from a poll_samples SQLite database."""

import argparse
import json
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from airpop.airports import lookup_airport

# --- Plot parameters (forkers: tweak these) ---
DATA_INTERVAL_HOURS = 1  # one chart point per this many hours
LABEL_INTERVAL_HOURS = 3  # show an axis label every this many hours
WINDOW_HOURS = 14  # Plot this many hours ending at the latest sample
# ---------------------------------------------

CHART_TEMPLATE = Path(__file__).with_name("chart_template.html")


def html_path_for_db(db_path: Path) -> Path:
    """e.g. data/KVGT.db -> data/KVGT.html"""
    return db_path.with_suffix(".html")


def parse_polled_at(value: str) -> datetime:
    """Parse UTC timestamp from DB"""
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def floor_to_interval(dt: datetime, interval_hours: int) -> datetime:
    """Truncate dt down to the start of its DATA_INTERVAL bucket."""
    hour = (dt.hour // interval_hours) * interval_hours
    return dt.replace(hour=hour, minute=0, second=0, microsecond=0)


def format_hour_label(dt: datetime) -> str:
    """e.g. 9am, 12pm, 2pm."""
    h = dt.hour
    if h == 0:
        return "12am"
    if h < 12:
        return f"{h}am"
    if h == 12:
        return "12pm"
    return f"{h - 12}pm"


def format_hour_window(start: datetime, interval_hours: int) -> str:
    """e.g. 12pm-1pm for a one-hour bucket starting at noon."""
    end = start + timedelta(hours=interval_hours)
    return f"{format_hour_label(start)}-{format_hour_label(end)}"


def load_series(db_path: Path, local_tz: str) -> tuple[list[str], list[str], list[int]]:
    """Return (axis_labels, hour_labels, counts) for the last WINDOW_HOURS."""
    tz = ZoneInfo(local_tz)
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT polled_at, count FROM poll_samples ORDER BY polled_at"
        ).fetchall()

    if not rows:
        return [], [], []

    parsed = [(parse_polled_at(polled_at), count) for polled_at, count in rows]
    cutoff = max(dt for dt, _ in parsed) - timedelta(hours=WINDOW_HOURS)

    buckets: dict[datetime, list[int]] = defaultdict(list)
    for polled_at, count in parsed:
        if polled_at < cutoff:
            continue
        local = polled_at.astimezone(tz)
        buckets[floor_to_interval(local, DATA_INTERVAL_HOURS)].append(count)

    axis_labels: list[str] = []
    hour_labels: list[str] = []
    counts: list[int] = []
    for when in sorted(buckets):
        counts.append(max(buckets[when]))
        hour_labels.append(format_hour_window(when, DATA_INTERVAL_HOURS))
        axis_labels.append(
            format_hour_label(when) if when.hour % LABEL_INTERVAL_HOURS == 0 else ""
        )
    return axis_labels, hour_labels, counts


def write_chart_html(
    axis_labels: list[str],
    hour_labels: list[str],
    counts: list[int],
    *,
    airport_icao: str,
    chart_title: str,
    output_path: Path,
    template_path: Path = CHART_TEMPLATE,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    template = template_path.read_text(encoding="utf-8")
    html = (
        template.replace("__CHART_TITLE__", chart_title)
        .replace("__AIRPORT_ICAO__", airport_icao)
        .replace("__AXIS_LABELS_JSON__", json.dumps(axis_labels))
        .replace("__HOUR_LABELS_JSON__", json.dumps(hour_labels))
        .replace("__COUNTS_JSON__", json.dumps(counts))
    )
    output_path.write_text(html, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot poll_samples to a static HTML chart.")
    parser.add_argument("db", type=Path, help="SQLite database (e.g. data/KVGT.db)")
    args = parser.parse_args()
    if not args.db.exists():
        raise SystemExit(f"Missing {args.db}")

    airport = lookup_airport(args.db.stem)
    output_path = html_path_for_db(args.db)
    axis_labels, hour_labels, counts = load_series(args.db, airport.timezone)
    write_chart_html(
        axis_labels,
        hour_labels,
        counts,
        airport_icao=airport.icao,
        chart_title=f"{airport.icao} Traffic",
        output_path=output_path,
    )
    print(f"wrote {output_path} ({len(counts)} points)")
    print(f"open {output_path.resolve()}")


if __name__ == "__main__":
    main()
