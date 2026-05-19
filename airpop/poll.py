"""One-shot OpenSky poll: count airborne aircraft in a bbox around a Class D airport."""

from opensky_api import OpenSkyApi

# KVGT (North Las Vegas) — (min_lat, max_lat, min_lon, max_lon)
KVGT_BBOX = (36.1607, 36.2607, -115.2444, -115.1444)


def count_planes_in_bbox() -> int:
    """Return count of aircraft in the KVGT bbox (not on ground)."""
    with OpenSkyApi() as api:
        result = api.get_states(bbox=KVGT_BBOX)

    if result is None:
        raise RuntimeError("OpenSky request failed or was rate-limited")

    count = 0
    for state in result.states:
        # skip aircraft with bad position data
        if state.longitude is None or state.latitude is None:
            continue
        if state.on_ground:
            continue
        count += 1

    return count


def main() -> None:
    print(count_planes_in_bbox())


if __name__ == "__main__":
    main()
