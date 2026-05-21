"""Build a static Chart.js page from a poll_samples SQLite database."""

import argparse
import json
import sqlite3
from pathlib import Path

CHART_TEMPLATE = Path(__file__).with_name("chart_template.html")


def html_path_for_db(db_path: Path) -> Path:
    """e.g. data/airport.db -> data/airport.html"""
    return db_path.with_suffix(".html")


def load_series(db_path: Path) -> tuple[list[str], list[int]]:
    """Return (labels, counts) ordered by polled_at."""
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT polled_at, count FROM poll_samples ORDER BY polled_at"
        ).fetchall()
    labels = [r[0][:16] for r in rows]  # trim ISO string for axis readability
    counts = [r[1] for r in rows]
    return labels, counts


def write_chart_html(
    labels: list[str],
    counts: list[int],
    *,
    db_path: Path,
    output_path: Path,
    template_path: Path = CHART_TEMPLATE,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    template = template_path.read_text(encoding="utf-8")
    html = (
        template.replace("__DB_PATH__", str(db_path))
        .replace("__LABELS_JSON__", json.dumps(labels))
        .replace("__COUNTS_JSON__", json.dumps(counts))
    )
    output_path.write_text(html, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot poll_samples to a static HTML chart.")
    parser.add_argument("db", type=Path, help="SQLite database (e.g. data/airport.db)")
    args = parser.parse_args()
    if not args.db.exists():
        raise SystemExit(f"Missing {args.db}")
    output_path = html_path_for_db(args.db)
    labels, counts = load_series(args.db)
    write_chart_html(labels, counts, db_path=args.db, output_path=output_path)
    print(f"wrote {output_path} ({len(counts)} points)")
    print(f"open {output_path.resolve()}")


if __name__ == "__main__":
    main()
