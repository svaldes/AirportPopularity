"""Build a static Chart.js page from a poll_samples SQLite database."""

import argparse
import json
import sqlite3
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import NamedTuple
from zoneinfo import ZoneInfo

from airpop.airports import lookup_airport

# --- Plot parameters (forkers: tweak these) ---
DATA_INTERVAL_HOURS = 1  # one chart point per this many hours
LABEL_INTERVAL_HOURS = 3  # show an axis label every this many hours
# Bar roles ("default" / "current"); colors live in chart_template.html
# ---------------------------------------------

CHART_TEMPLATE = Path(__file__).with_name("chart_template.html")
HOURS_PER_DAY = 24


class ChartSeries(NamedTuple):
    axis_labels: list[str]
    hour_labels: list[str]
    peak_counts: list[int | None]  # peak traffic count per hour; None if no samples
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


def format_hour_label(hour: int) -> str:
    """e.g. 9am, 12pm, 2pm."""
    h = hour % 24
    if h == 0:
        return "12am"
    if h < 12:
        return f"{h}am"
    if h == 12:
        return "12pm"
    return f"{h - 12}pm"


def format_date_label(day: date) -> str:
    """e.g. Sun, Aug 23, 2026."""
    return day.strftime("%a, %b ") + str(day.day) + day.strftime(", %Y")


def resolve_chart_day(local_tz: str, on_date: date | None) -> date:
    """Airport-local calendar day; future dates clamp to today."""
    today = datetime.now(ZoneInfo(local_tz)).date()
    day = on_date or today
    return today if day > today else day


def day_nav_hrefs(day: date, *, today: date) -> tuple[str, str, str]:
    """Return (prev_href, next_href_or_empty, date_label). Next empty when day is today."""
    prev = day - timedelta(days=1)
    prev_href = f"/?date={prev.isoformat()}"
    next_href = (
        ""
        if day >= today
        else f"/?date={(day + timedelta(days=1)).isoformat()}"
    )
    return prev_href, next_href, format_date_label(day)


def format_hour_window(hour: int, interval_hours: int) -> str:
    """e.g. 12pm-1pm for a one-hour bucket starting at noon."""
    return f"{format_hour_label(hour)}-{format_hour_label(hour + interval_hours)}"


def load_series(
    db_path: Path,
    local_tz: str,
    *,
    on_date: date | None = None,
) -> ChartSeries:
    """Return chart series for one local calendar day (midnight–midnight)."""
    tz = ZoneInfo(local_tz)
    now_local = datetime.now(tz)
    day = resolve_chart_day(local_tz, on_date)
    now_bucket = floor_to_interval(now_local, DATA_INTERVAL_HOURS)

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT polled_at, count FROM poll_samples ORDER BY polled_at"
        ).fetchall()

    # (date, hour) -> sample counts in that local hour
    buckets: dict[tuple[date, int], list[int]] = defaultdict(list)
    for polled_at, count in rows:
        local = parse_polled_at(polled_at).astimezone(tz)
        bucket = floor_to_interval(local, DATA_INTERVAL_HOURS)
        buckets[(bucket.date(), bucket.hour)].append(count)

    # Show the current hour on today even if no polls have landed yet.
    if day == now_local.date():
        buckets.setdefault((day, now_bucket.hour), [0])

    axis_labels: list[str] = []
    hour_labels: list[str] = []
    peak_counts: list[int | None] = []
    bar_roles: list[str] = []
    for hour in range(0, HOURS_PER_DAY, DATA_INTERVAL_HOURS):
        samples = buckets.get((day, hour))
        peak_counts.append(max(samples) if samples else None)
        hour_labels.append(format_hour_window(hour, DATA_INTERVAL_HOURS))
        axis_labels.append(
            format_hour_label(hour) if hour % LABEL_INTERVAL_HOURS == 0 else ""
        )
        is_current = day == now_local.date() and hour == now_bucket.hour
        bar_roles.append("current" if is_current else "default")
    return ChartSeries(axis_labels, hour_labels, peak_counts, bar_roles)


def render_chart_html(
    series: ChartSeries,
    *,
    airport_icao: str,
    chart_title: str,
    on_date: date,
    local_tz: str,
    refresh_seconds: int | None = None,
    template_path: Path = CHART_TEMPLATE,
) -> str:
    """Fill the chart template; optional browser refresh interval for the live server."""
    today = datetime.now(ZoneInfo(local_tz)).date()
    prev_href, next_href, date_label = day_nav_hrefs(on_date, today=today)
    if next_href:
        next_html = f'<a class="day-nav-next" href="{next_href}" aria-label="Next day">›</a>'
    else:
        next_html = '<span class="day-nav-next disabled" aria-disabled="true">›</span>'

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
        .replace("__DATE_LABEL__", date_label)
        .replace("__PREV_HREF__", prev_href)
        .replace("__NEXT_HTML__", next_html)
        .replace("__AXIS_LABELS_JSON__", json.dumps(series.axis_labels))
        .replace("__HOUR_LABELS_JSON__", json.dumps(series.hour_labels))
        .replace("__COUNTS_JSON__", json.dumps(series.peak_counts))
        .replace("__BAR_ROLES_JSON__", json.dumps(series.bar_roles))
    )


def chart_html_for_db(
    db_path: Path,
    *,
    on_date: date | None = None,
    refresh_seconds: int | None = None,
    template_path: Path = CHART_TEMPLATE,
) -> str:
    """Load series and render HTML (styling lives in the chart template)."""
    airport = lookup_airport(db_path.stem)
    day = resolve_chart_day(airport.timezone, on_date)
    series = load_series(db_path, airport.timezone, on_date=day)
    return render_chart_html(
        series,
        airport_icao=airport.icao,
        chart_title=f"{airport.icao} Traffic",
        on_date=day,
        local_tz=airport.timezone,
        refresh_seconds=refresh_seconds,
        template_path=template_path,
    )


def write_chart_html(
    db_path: Path,
    *,
    output_path: Path,
    on_date: date | None = None,
    template_path: Path = CHART_TEMPLATE,
) -> ChartSeries:
    """Render chart HTML to disk; returns the series (for CLI point count)."""
    airport = lookup_airport(db_path.stem)
    day = resolve_chart_day(airport.timezone, on_date)
    series = load_series(db_path, airport.timezone, on_date=day)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    html = render_chart_html(
        series,
        airport_icao=airport.icao,
        chart_title=f"{airport.icao} Traffic",
        on_date=day,
        local_tz=airport.timezone,
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
    points = sum(1 for c in series.peak_counts if c is not None)
    print(f"wrote {output_path} ({points} hours with data)")
    print(f"open {output_path.resolve()}")


if __name__ == "__main__":
    main()
