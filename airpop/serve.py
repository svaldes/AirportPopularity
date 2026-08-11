"""Local HTTP server: serve a live chart that rebuilds from the DB on each request."""

import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer

from airpop.airports import lookup_airport
from airpop.collector import POLL_INTERVAL_SEC
from airpop.db import db_path_for
from airpop.tools.plot import chart_html_for_db

DEFAULT_PORT = 8000


def build_chart_page(icao: str, *, refresh_seconds: int) -> bytes:
    airport = lookup_airport(icao)
    db_path = db_path_for(airport.icao)
    if not db_path.exists():
        body = (
            f"<h1>{airport.icao}</h1>"
            f"<p>No database at <code>{db_path}</code>. "
            f"Start the collector: <code>uv run collect {airport.icao}</code></p>"
        )
        return body.encode("utf-8")

    return chart_html_for_db(db_path, refresh_seconds=refresh_seconds).encode("utf-8")


def make_handler(icao: str, refresh_seconds: int) -> type[BaseHTTPRequestHandler]:
    class ChartHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/favicon.ico":
                self.send_response(204)
                self.end_headers()
                return
            if self.path not in ("/", f"/{icao}", f"/{icao}/"):
                self.send_error(404, "Not found - try /")
                return
            body = build_chart_page(icao, refresh_seconds=refresh_seconds)
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
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port to listen on (default {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--refresh",
        type=int,
        default=POLL_INTERVAL_SEC,
        help=f"Browser auto-refresh seconds (default {POLL_INTERVAL_SEC})",
    )
    args = parser.parse_args()
    airport = lookup_airport(args.icao)
    handler = make_handler(airport.icao, args.refresh)
    server = HTTPServer(("127.0.0.1", args.port), handler)
    print(f"serving {airport.icao} at http://127.0.0.1:{args.port}/  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
        server.server_close()


if __name__ == "__main__":
    main()
