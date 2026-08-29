"""OpenSky Network: count airborne aircraft in a degree bbox."""

from opensky_api import OpenSkyApi

from airpop.config import BBOX_DELTA_DEG

FT_PER_M = 3.28084


def bbox_from_center(
    lat: float, lon: float, delta: float = BBOX_DELTA_DEG
) -> tuple[float, float, float, float]:
    """OpenSky bbox: (min_lat, max_lat, min_lon, max_lon)."""
    return (lat - delta, lat + delta, lon - delta, lon + delta)


def count_airborne(
    lat: float, lon: float, *, max_msl_ft: float, delta: float = BBOX_DELTA_DEG
) -> int:
    """Count aircraft in the bbox at or below max_msl_ft, not on ground."""
    bbox = bbox_from_center(lat, lon, delta)
    with OpenSkyApi() as api:
        result = api.get_states(bbox=bbox)

    if result is None:
        raise RuntimeError("OpenSky request failed or was rate-limited")

    count = 0
    for state in result.states:
        if state.longitude is None or state.latitude is None:
            continue
        if state.on_ground:
            continue
        if state.baro_altitude is None:
            continue
        if state.baro_altitude * FT_PER_M > max_msl_ft:
            continue
        count += 1
    return count
