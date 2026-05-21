"""Poll OpenSky on a fixed interval and log counts to SQLite."""

import time
from datetime import datetime, timezone

from airpop.db import insert_poll_sample
from airpop.poll import count_planes_in_bbox

# (icao, lat, lon) — KVGT North Las Vegas
AIRPORT = ("KVGT", 36.2107, -115.1944)

# 360 calls/day; OpenSky anonymous states bucket is 400/day.
POLL_INTERVAL_SEC = 4 * 60


def run_collector() -> None:
    icao, lat, lon = AIRPORT
    while True:
        ts = datetime.now(timezone.utc).isoformat()
        try:
            n = count_planes_in_bbox(lat, lon)
            insert_poll_sample(n, airport_icao=icao)
            print(f"{ts}  count={n}  saved")
        except RuntimeError as e:
            print(f"{ts}  error={e}")
        time.sleep(POLL_INTERVAL_SEC)


def main() -> None:
    try:
        run_collector()
    except KeyboardInterrupt:
        print("stopped")


if __name__ == "__main__":
    main()
