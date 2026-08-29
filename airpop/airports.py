"""Load airport records from airports.json."""

import json
from pathlib import Path
from typing import NamedTuple

AIRPORTS_PATH = Path(__file__).resolve().parent.parent / "airports.json"


class Airport(NamedTuple):
    icao: str
    name: str
    lat: float
    lon: float
    elevation_ft: int  # surveyed field elevation, MSL
    timezone: str  # IANA name, e.g. America/Los_Angeles (handles DST)


def load_airports() -> dict[str, dict]:
    """Return raw {ICAO: {...}, ...} from the repo seed file."""
    return json.loads(AIRPORTS_PATH.read_text(encoding="utf-8"))


def lookup_airport(icao: str) -> Airport:
    """Return an Airport for a code in airports.json."""
    icao = icao.upper()
    airports = load_airports()
    try:
        entry = airports[icao]
    except KeyError as e:
        known = ", ".join(sorted(airports))
        raise KeyError(f"Unknown airport {icao!r}; seed file has: {known}") from e
    return Airport(
        icao=icao,
        name=str(entry["name"]),
        lat=float(entry["lat"]),
        lon=float(entry["lon"]),
        elevation_ft=int(entry["elevation_ft"]),
        timezone=str(entry["timezone"]),
    )
