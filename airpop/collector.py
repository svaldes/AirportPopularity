"""Poll an ADS-B source on a fixed interval and log counts to SQLite."""

import argparse
import time
from datetime import datetime, timezone

from airpop.airports import lookup_airport
from airpop.config import POLL_INTERVAL_SEC
from airpop.db import db_path_for, insert_poll_sample
from airpop.sources import count_airborne, resolve_source_name


def run_collector(icao: str) -> None:
    airport = lookup_airport(icao)
    source = resolve_source_name()
    path = db_path_for(airport.icao)
    print(f"collecting {airport.icao} via {source} → {path} (every {POLL_INTERVAL_SEC}s)")
    while True:
        ts = datetime.now(timezone.utc).isoformat()
        try:
            n = count_airborne(airport.lat, airport.lon)
            insert_poll_sample(n, path=path)
            print(f"{ts}  count={n}  saved")
        except RuntimeError as e:
            print(f"{ts}  error={e}")
        time.sleep(POLL_INTERVAL_SEC)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Poll AIRPOP_SOURCE on an interval; log to data/<ICAO>.db"
    )
    parser.add_argument("icao", help="Airport ICAO code (e.g. KVGT)")
    args = parser.parse_args()
    try:
        run_collector(args.icao)
    except KeyboardInterrupt:
        print("stopped")


if __name__ == "__main__":
    main()
