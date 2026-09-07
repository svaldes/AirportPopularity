"""Pluggable ADS-B sources. Selected by required AIRPOP_SOURCE env var."""

from __future__ import annotations

import os
from collections.abc import Callable

# (airborne, on_ground) from one source fetch
CountFn = Callable[..., tuple[int, int]]


def resolve_source_name() -> str:
    raw = os.environ.get("AIRPOP_SOURCE")
    if raw is None or not raw.strip():
        raise RuntimeError(
            "AIRPOP_SOURCE is not set; expected opensky, adsbx, or local"
        )
    return raw.strip().lower()


def get_count_in_volume() -> CountFn:
    """Return count_in_volume(lat, lon, *, max_msl_ft) for AIRPOP_SOURCE."""
    name = resolve_source_name()
    if name == "opensky":
        from airpop.sources.opensky import count_in_volume

        return count_in_volume
    if name == "adsbx":
        from airpop.sources.adsbx import count_in_volume

        return count_in_volume
    if name == "local":
        raise RuntimeError("AIRPOP_SOURCE=local is not implemented yet")
    raise RuntimeError(
        f"Unknown AIRPOP_SOURCE={name!r}; expected opensky, adsbx, or local"
    )


def count_in_volume(lat: float, lon: float, *, max_msl_ft: float) -> tuple[int, int]:
    """Airborne and on-ground counts in the source volume (AIRPOP_SOURCE)."""
    return get_count_in_volume()(lat, lon, max_msl_ft=max_msl_ft)
