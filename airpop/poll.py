"""One-shot aircraft count for an airport (source from AIRPOP_SOURCE)."""

import argparse

from airpop.airports import lookup_airport
from airpop.config import ceiling_msl_ft
from airpop.sources import count_in_volume


def main() -> None:
    parser = argparse.ArgumentParser(
        description="One-shot aircraft count for an airport (AIRPOP_SOURCE)"
    )
    parser.add_argument("icao", help="Airport ICAO code (e.g. KVGT)")
    args = parser.parse_args()
    airport = lookup_airport(args.icao)
    airborne, on_ground = count_in_volume(
        airport.lat,
        airport.lon,
        max_msl_ft=ceiling_msl_ft(airport.elevation_ft),
    )
    print(f"{airborne} airborne, {on_ground} on ground")


if __name__ == "__main__":
    main()
