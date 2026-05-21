"""OpenSky poll: count airborne aircraft in a bbox around a point."""

from opensky_api import OpenSkyApi

# Half-width of bounding box in degrees (~3 NM latitude)
BBOX_DELTA_DEG = 0.05


def bbox_from_center(lat: float, lon: float, delta: float = BBOX_DELTA_DEG) -> tuple[float, float, float, float]:
    """OpenSky bbox: (min_lat, max_lat, min_lon, max_lon)."""
    return (lat - delta, lat + delta, lon - delta, lon + delta)


def count_planes_in_bbox(lat: float, lon: float, delta: float = BBOX_DELTA_DEG) -> int:
    """Return count of aircraft in the bbox around (lat, lon), not on ground."""
    bbox = bbox_from_center(lat, lon, delta)
    with OpenSkyApi() as api:
        result = api.get_states(bbox=bbox)

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
    from airpop.collector import AIRPORT

    _, lat, lon = AIRPORT
    print(count_planes_in_bbox(lat, lon))


if __name__ == "__main__":
    main()
