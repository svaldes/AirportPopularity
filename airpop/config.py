"""Shared collector / chart parameters """

# ~288 calls/day; fits OpenSky anonymous (~400/day) and ADSBX Community (~10k/month).
POLL_INTERVAL_SEC = 5 * 60

# Horizontal disk around the airport. OpenSky uses a degree bbox; 1° lat ≈ 60 NM.
DISK_NM = 3
BBOX_DELTA_DEG = DISK_NM / 60

# Count aircraft at or below field elevation + this (AGL).
CEILING_AGL_FT = 1500


def ceiling_msl_ft(elevation_ft: int) -> int:
    """MSL cap used in the collector and the info tip."""
    return elevation_ft + CEILING_AGL_FT

