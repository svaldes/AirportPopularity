"""OpenSky Network: count aircraft in a degree bbox."""

from opensky_api import OpenSkyApi

from airpop.config import BBOX_DELTA_DEG

FT_PER_M = 3.28084


def bbox_from_center(
    lat: float, lon: float, delta: float = BBOX_DELTA_DEG
) -> tuple[float, float, float, float]:
    """OpenSky bbox: (min_lat, max_lat, min_lon, max_lon)."""
    return (lat - delta, lat + delta, lon - delta, lon + delta)


def count_in_volume(
    lat: float, lon: float, *, max_msl_ft: float, delta: float = BBOX_DELTA_DEG
) -> tuple[int, int]:
    """Count airborne (at or below max_msl_ft) and on-ground aircraft in the bbox."""
    bbox = bbox_from_center(lat, lon, delta)
    with OpenSkyApi() as api:
        result = api.get_states(bbox=bbox)

    if result is None:
        raise RuntimeError("OpenSky request failed or was rate-limited")

    airborne = 0
    on_ground = 0
    for state in result.states:
        if state.longitude is None or state.latitude is None:
            continue
        if state.on_ground:
            on_ground += 1
            continue
        if state.baro_altitude is None:
            continue
        if state.baro_altitude * FT_PER_M > max_msl_ft:
            continue
        airborne += 1
    return airborne, on_ground
