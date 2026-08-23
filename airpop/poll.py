"""One-shot aircraft count for an airport (source from AIRPOP_SOURCE)."""

import argparse

from airpop.airports import lookup_airport
from airpop.sources import count_airborne


def main() -> None:
    parser = argparse.ArgumentParser(
        description="One-shot aircraft count for an airport (AIRPOP_SOURCE)"
    )
    parser.add_argument("icao", help="Airport ICAO code (e.g. KVGT)")
    args = parser.parse_args()
    airport = lookup_airport(args.icao)
    print(count_airborne(airport.lat, airport.lon))


if __name__ == "__main__":
    main()
