"""Build a static Chart.js page from a poll_samples SQLite database."""

import argparse
import json
import sqlite3
import statistics
from collections import defaultdict
from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import NamedTuple
from zoneinfo import ZoneInfo

from airpop.airports import lookup_airport
from airpop.collector import POLL_INTERVAL_SEC

# --- Plot parameters (forkers: tweak these) ---
DATA_INTERVAL_MINUTES = 120  # bar width / bucket size; one chart point each
LABEL_INTERVAL_MINUTES = 120 * 2  # show an axis label every this many minutes
# Bar roles ("default" / "current"); colors live in chart_template.html
# ---------------------------------------------

CHART_TEMPLATE = Path(__file__).with_name("chart_template.html")
MINUTES_PER_DAY = 24 * 60


def validate_interval_minutes(slot_mins: int = DATA_INTERVAL_MINUTES) -> int:
    """Ensure the data interval divides a day evenly."""
    if slot_mins <= 0 or MINUTES_PER_DAY % slot_mins != 0:
        raise ValueError(
            f"DATA_INTERVAL_MINUTES={slot_mins} must be > 0 and divide {MINUTES_PER_DAY}"
        )
    return slot_mins


def expected_samples_per_slot(slot_mins: int = DATA_INTERVAL_MINUTES) -> int:
    """Polls needed to treat a slot as complete (for peaks / typical)."""
    slot_secs = slot_mins * 60
    if slot_secs % POLL_INTERVAL_SEC != 0:
        raise ValueError(
            f"slot {slot_mins}m must be a multiple of POLL_INTERVAL_SEC={POLL_INTERVAL_SEC}"
        )
    return slot_secs // POLL_INTERVAL_SEC

TypicalAggregator = Callable[[list[int]], float]


def aggregate_typical_mean(values: list[int]) -> float:
    """Uniform average of same-weekday slot peaks (swap for other weightings)."""
    return statistics.mean(values)


class ChartSeries(NamedTuple):
    axis_labels: list[str]
    hour_labels: list[str]
    peak_counts: list[int | None]  # measured peak traffic count; None if no samples
    typical_counts: list[float | None]  # same-weekday typical; None if no history
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


def floor_to_slot_minutes(dt: datetime, slot_mins: int) -> int:
    """Minutes from local midnight at the start of dt's data interval."""
    minutes = dt.hour * 60 + dt.minute
    return (minutes // slot_mins) * slot_mins


def format_clock_label(minutes: int) -> str:
    """e.g. 9am, 1:30pm, 12am."""
    minutes = minutes % MINUTES_PER_DAY
    h, m = divmod(minutes, 60)
    if h == 0:
        base = "12"
        suffix = "am"
    elif h < 12:
        base = str(h)
        suffix = "am"
    elif h == 12:
        base = "12"
        suffix = "pm"
    else:
        base = str(h - 12)
        suffix = "pm"
    if m:
        return f"{base}:{m:02d}{suffix}"
    return f"{base}{suffix}"


def format_date_label(day: date) -> str:
    """e.g. Sun, Aug 23, 2026."""
    return day.strftime("%a, %b ") + str(day.day) + day.strftime(", %Y")


def resolve_chart_day(local_tz: str, on_date: date | None) -> date:
    """Airport-local calendar day; future dates clamp to today."""
    today = datetime.now(ZoneInfo(local_tz)).date()
    day = on_date or today
    return today if day > today else day


def day_nav_hrefs(day: date, *, today: date) -> tuple[str, str, str, str]:
    """Return (prev_href, next_href, today_href, date_label).

    next_href / today_href are empty when day is already today.
    """
    prev = day - timedelta(days=1)
    prev_href = f"/?date={prev.isoformat()}"
    today_href = f"/?date={today.isoformat()}"
    if day >= today:
        return prev_href, "", "", format_date_label(day)
    next_href = f"/?date={(day + timedelta(days=1)).isoformat()}"
    return prev_href, next_href, today_href, format_date_label(day)


def format_slot_window(start_minutes: int, slot_mins: int) -> str:
    """e.g. 12pm-1:30pm for a 1.5h bucket starting at noon."""
    return (
        f"{format_clock_label(start_minutes)}-"
        f"{format_clock_label(start_minutes + slot_mins)}"
    )


def load_series(
    db_path: Path,
    local_tz: str,
    *,
    on_date: date | None = None,
    aggregate_typical: TypicalAggregator = aggregate_typical_mean,
) -> ChartSeries:
    """Return chart series for one local calendar day (midnight–midnight)."""
    slot_mins = validate_interval_minutes()
    label_every_mins = LABEL_INTERVAL_MINUTES
    tz = ZoneInfo(local_tz)
    now_local = datetime.now(tz)
    day = resolve_chart_day(local_tz, on_date)
    now_slot = floor_to_slot_minutes(now_local, slot_mins)

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT polled_at, count FROM poll_samples ORDER BY polled_at"
        ).fetchall()

    # (date, slot_start_minutes) -> sample counts in that local bucket
    buckets: dict[tuple[date, int], list[int]] = defaultdict(list)
    for polled_at, count in rows:
        local = parse_polled_at(polled_at).astimezone(tz)
        slot = floor_to_slot_minutes(local, slot_mins)
        buckets[(local.date(), slot)].append(count)

    expected = expected_samples_per_slot(slot_mins)
    # Complete slots only — feed measured history and typical.
    slot_peak: dict[tuple[date, int], int] = {
        key: max(samples)
        for key, samples in buckets.items()
        if len(samples) >= expected
    }

    weekday = day.weekday()
    viewing_today = day == now_local.date()
    axis_labels: list[str] = []
    hour_labels: list[str] = []
    peak_counts: list[int | None] = []
    typical_counts: list[float | None] = []
    bar_roles: list[str] = []
    for start in range(0, MINUTES_PER_DAY, slot_mins):
        is_current = viewing_today and start == now_slot
        peak = slot_peak.get((day, start))
        if peak is None and is_current:
            live = buckets.get((day, start), [])
            peak = max(live) if live else 0
        peak_counts.append(peak)
        same_dow_peaks = [
            peak
            for (d, slot), peak in slot_peak.items()
            if slot == start and d.weekday() == weekday
        ]
        typical_counts.append(
            aggregate_typical(same_dow_peaks) if same_dow_peaks else None
        )
        hour_labels.append(format_slot_window(start, slot_mins))
        axis_labels.append(
            format_clock_label(start) if start % label_every_mins == 0 else ""
        )
        bar_roles.append("current" if is_current else "default")
    return ChartSeries(
        axis_labels, hour_labels, peak_counts, typical_counts, bar_roles
    )


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
    prev_href, next_href, today_href, date_label = day_nav_hrefs(on_date, today=today)
    if next_href:
        next_html = f'<a class="day-nav-next" href="{next_href}" aria-label="Next day">›</a>'
    else:
        next_html = '<span class="day-nav-next disabled" aria-disabled="true">›</span>'
    if today_href:
        today_html = (
            f'<a class="day-nav-today" href="{today_href}" aria-label="Today">»</a>'
        )
    else:
        today_html = (
            '<span class="day-nav-today disabled" aria-disabled="true">»</span>'
        )

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
        .replace("__TODAY_HTML__", today_html)
        .replace("__AXIS_LABELS_JSON__", json.dumps(series.axis_labels))
        .replace("__HOUR_LABELS_JSON__", json.dumps(series.hour_labels))
        .replace("__COUNTS_JSON__", json.dumps(series.peak_counts))
        .replace("__TYPICAL_JSON__", json.dumps(series.typical_counts))
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
    print(f"wrote {output_path} ({points} slots with data)")
    print(f"open {output_path.resolve()}")


if __name__ == "__main__":
    main()
