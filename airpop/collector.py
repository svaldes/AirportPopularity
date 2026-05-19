"""Poll OpenSky on a fixed interval"""

import time
from datetime import datetime, timezone

from airpop.poll import count_planes_in_bbox

# 360 calls/day; OpenSky anonymous states bucket is 400/day.
POLL_INTERVAL_SEC = 4 * 60


def run_collector() -> None:
    while True:
        ts = datetime.now(timezone.utc).isoformat()
        try:
            n = count_planes_in_bbox()
            print(f"{ts}  count={n}")
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
