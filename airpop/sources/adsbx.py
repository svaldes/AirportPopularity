"""ADS-B Exchange Community API (RapidAPI): count airborne aircraft in an NM radius."""

import json
import os
import urllib.error
import urllib.request

from airpop.config import DISK_NM


def count_airborne(
    lat: float, lon: float, *, max_msl_ft: float, dist_nm: float = DISK_NM
) -> int:
    """Count aircraft within dist_nm at or below max_msl_ft, not on ground."""
    key = os.environ.get("ADSBX_RAPIDAPI_KEY", "").strip()
    host = os.environ.get("ADSBX_RAPIDAPI_HOST", "").strip()
    if not key or not host:
        raise RuntimeError(
            "AIRPOP_SOURCE=adsbx requires ADSBX_RAPIDAPI_KEY and ADSBX_RAPIDAPI_HOST"
        )

    url = f"https://{host}/v2/lat/{lat}/lon/{lon}/dist/{dist_nm}/"
    request = urllib.request.Request(
        url,
        headers={
            "X-RapidAPI-Key": key,
            "X-RapidAPI-Host": host,
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"ADS-B Exchange HTTP {e.code}: {body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"ADS-B Exchange request failed: {e}") from e

    aircraft = payload.get("ac") or []
    count = 0
    for ac in aircraft:
        if ac.get("lat") is None or ac.get("lon") is None:
            continue
        # ADSBX uses the string "ground" for on-ground targets.
        if ac.get("alt_baro") == "ground":
            continue
        try:
            alt_ft = float(ac.get("alt_baro"))
        except (TypeError, ValueError):
            continue
        if alt_ft > max_msl_ft:
            continue
        count += 1
    return count
