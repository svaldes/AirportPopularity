"""Build a static Chart.js page from a poll_samples SQLite database."""

import argparse
import json
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import NamedTuple
from zoneinfo import ZoneInfo

from airpop.airports import lookup_airport

# --- Plot parameters (forkers: tweak these) ---
DATA_INTERVAL_HOURS = 1  # one chart point per this many hours
LABEL_INTERVAL_HOURS = 3  # show an axis label every this many hours
WINDOW_HOURS = 14  # Plot this many hours ending at the latest sample
# Bar roles ("default" / "current"); colors live in chart_template.html
# ---------------------------------------------

CHART_TEMPLATE = Path(__file__).with_name("chart_template.html")


class ChartSeries(NamedTuple):
    axis_labels: list[str]
    hour_labels: list[str]
    counts: list[int]
    bar_roles: list[str]  # e.g. "default" or "current" — styled in the template


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


def load_series(db_path: Path, local_tz: str) -> ChartSeries:
    """Return chart series for the last WINDOW_HOURS"""
    tz = ZoneInfo(local_tz)
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT polled_at, count FROM poll_samples ORDER BY polled_at"
        ).fetchall()

    if not rows:
        return ChartSeries([], [], [], [])

    parsed = [(parse_polled_at(polled_at), count) for polled_at, count in rows]
    cutoff = max(dt for dt, _ in parsed) - timedelta(hours=WINDOW_HOURS)
    now_local = datetime.now(tz)
    now_bucket = floor_to_interval(now_local, DATA_INTERVAL_HOURS)

    buckets: dict[datetime, list[int]] = defaultdict(list)
    for polled_at, count in parsed:
        if polled_at < cutoff:
            continue
        local = polled_at.astimezone(tz)
        buckets[floor_to_interval(local, DATA_INTERVAL_HOURS)].append(count)

    # Show the current hour even if no polls have landed in it yet.
    if now_local.astimezone(timezone.utc) >= cutoff:
        buckets.setdefault(now_bucket, [0])

    axis_labels: list[str] = []
    hour_labels: list[str] = []
    counts: list[int] = []
    bar_roles: list[str] = []
    for when in sorted(buckets):
        counts.append(max(buckets[when]))
        hour_labels.append(format_hour_window(when, DATA_INTERVAL_HOURS))
        axis_labels.append(
            format_hour_label(when) if when.hour % LABEL_INTERVAL_HOURS == 0 else ""
        )
        bar_roles.append("current" if when == now_bucket else "default")
    return ChartSeries(axis_labels, hour_labels, counts, bar_roles)


def render_chart_html(
    series: ChartSeries,
    *,
    airport_icao: str,
    chart_title: str,
    refresh_seconds: int | None = None,
    template_path: Path = CHART_TEMPLATE,
) -> str:
    """Fill the chart template; optional browser refresh interval for the live server."""
    refresh_meta = (
        f'<meta http-equiv="refresh" content="{refresh_seconds}">'
        if refresh_seconds
        else ""
    )
    template = template_path.read_text(encoding="utf-8")
    return (
        template.replace("__REFRESH_META__", refresh_meta)
        .replace("__CHART_TITLE__", chart_title)
        .replace("__AIRPORT_ICAO__", airport_icao)
        .replace("__AXIS_LABELS_JSON__", json.dumps(series.axis_labels))
        .replace("__HOUR_LABELS_JSON__", json.dumps(series.hour_labels))
        .replace("__COUNTS_JSON__", json.dumps(series.counts))
        .replace("__BAR_ROLES_JSON__", json.dumps(series.bar_roles))
    )


def chart_html_for_db(
    db_path: Path,
    *,
    refresh_seconds: int | None = None,
    template_path: Path = CHART_TEMPLATE,
) -> str:
    """Load series and render HTML (styling lives in the chart template)."""
    airport = lookup_airport(db_path.stem)
    series = load_series(db_path, airport.timezone)
    return render_chart_html(
        series,
        airport_icao=airport.icao,
        chart_title=f"{airport.icao} Traffic",
        refresh_seconds=refresh_seconds,
        template_path=template_path,
    )


def write_chart_html(
    db_path: Path,
    *,
    output_path: Path,
    template_path: Path = CHART_TEMPLATE,
) -> ChartSeries:
    """Render chart HTML to disk; returns the series (for CLI point count)."""
    airport = lookup_airport(db_path.stem)
    series = load_series(db_path, airport.timezone)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    html = render_chart_html(
        series,
        airport_icao=airport.icao,
        chart_title=f"{airport.icao} Traffic",
        template_path=template_path,
    )
    output_path.write_text(html, encoding="utf-8")
    return series


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot poll_samples to a static HTML chart.")
    parser.add_argument("db", type=Path, help="SQLite database (e.g. data/KVGT.db)")
    args = parser.parse_args()
    if not args.db.exists():
        raise SystemExit(f"Missing {args.db}")

    output_path = html_path_for_db(args.db)
    series = write_chart_html(args.db, output_path=output_path)
    print(f"wrote {output_path} ({len(series.counts)} points)")
    print(f"open {output_path.resolve()}")


if __name__ == "__main__":
    main()
