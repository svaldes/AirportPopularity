"""One-shot OpenSky poll: count airborne aircraft in a bbox around a Class D airport."""

import json
import urllib.error
import urllib.request

# KVGT (North Las Vegas)
LAMIN = 36.1607
LAMAX = 36.2607
LOMIN = -115.2444
LOMAX = -115.1444

OPENSKY_URL = (
    "https://opensky-network.org/api/states/all"
    f"?lamin={LAMIN}&lomin={LOMIN}&lamax={LAMAX}&lomax={LOMAX}"
)

# State vector indices (https://openskynetwork.github.io/opensky-api/rest.html)
LON = 5
LAT = 6
ON_GROUND = 8


def count_planes_in_bbox() -> int:
    """Return count of aircraft in the KVGT bbox (not on ground)."""
    try:
        with urllib.request.urlopen(OPENSKY_URL, timeout=30) as response:
            body = response.read().decode()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"OpenSky HTTP {e.code}: {e.reason}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"OpenSky request failed: {e.reason}") from e

    data = json.loads(body)
    states = data.get("states") or []

    count = 0
    for row in states:
        lon = row[LON]
        lat = row[LAT]
        if lon is None or lat is None:
            continue
        if row[ON_GROUND]:
            continue
        count += 1

    return count


if __name__ == "__main__":
    print(count_planes_in_bbox())
