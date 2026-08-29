"""Local HTTP server: serve a live chart that rebuilds from the DB on each request."""

import argparse
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from airpop.airports import lookup_airport
from airpop.collector import POLL_INTERVAL_SEC
from airpop.db import db_path_for
from airpop.tools.plot import chart_html, chart_json

DEFAULT_PORT = 8000


def parse_on_date(query: dict[str, list[str]]) -> date | None:
    """Parse ?date=YYYY-MM-DD; invalid values ignored (caller uses today)."""
    raw_list = query.get("date")
    if not raw_list:
        return None
    raw = raw_list[0].strip()
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def parse_embed(query: dict[str, list[str]]) -> bool:
    """True when ?embed=1 (compact mast for iframe hosts)."""
    raw_list = query.get("embed")
    if not raw_list:
        return False
    return raw_list[0].strip() == "1"


def parse_poll(query: dict[str, list[str]]) -> bool:
    """True when ?poll=1 (series payload for in-page polling)."""
    raw_list = query.get("poll")
    if not raw_list:
        return False
    return raw_list[0].strip() == "1"


def build_chart_page(
    icao: str,
    *,
    refresh_seconds: int,
    on_date: date | None = None,
    embed: bool = False,
) -> bytes:
    airport = lookup_airport(icao)
    db_path = db_path_for(airport.icao)
    if not db_path.exists():
        body = (
            f"<h1>{airport.icao}</h1>"
            f"<p>No database at <code>{db_path}</code>. "
            f"Start the collector: <code>uv run collect {airport.icao}</code></p>"
        )
        return body.encode("utf-8")

    return chart_html(
        db_path,
        on_date=on_date,
        refresh_seconds=refresh_seconds,
        embed=embed,
    ).encode("utf-8")


def make_handler(icao: str, refresh_seconds: int) -> type[BaseHTTPRequestHandler]:
    class ChartHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path
            if path == "/favicon.ico":
                self.send_response(204)
                self.end_headers()
                return
            if path not in ("/", f"/{icao}", f"/{icao}/"):
                self.send_error(404, "Not found - try /")
                return
            query = parse_qs(parsed.query)
            on_date = parse_on_date(query)
            embed = parse_embed(query)
            if parse_poll(query):
                airport = lookup_airport(icao)
                db_path = db_path_for(airport.icao)
                if not db_path.exists():
                    self.send_error(404, "No database")
                    return
                body = chart_json(db_path, on_date=on_date).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            body = build_chart_page(
                icao,
                refresh_seconds=refresh_seconds,
                on_date=on_date,
                embed=embed,
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            print("%s - %s" % (self.address_string(), format % args))

    return ChartHandler


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Serve a live traffic chart (rebuilds from data/<ICAO>.db on each load)."
    )
    parser.add_argument("icao", help="Airport ICAO code (e.g. KVGT)")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind address (default 127.0.0.1; use 0.0.0.0 for external access)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port to listen on (default {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--refresh",
        type=int,
        default=POLL_INTERVAL_SEC,
        help=f"Browser poll interval in seconds (default {POLL_INTERVAL_SEC}; 0 disables)",
    )
    args = parser.parse_args()
    airport = lookup_airport(args.icao)
    handler = make_handler(airport.icao, args.refresh)
    server = HTTPServer((args.host, args.port), handler)
    print(f"serving {airport.icao} at http://{args.host}:{args.port}/  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
        server.server_close()


if __name__ == "__main__":
    main()
