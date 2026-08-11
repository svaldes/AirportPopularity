# Airport Popularity

Estimate how busy a small airport’s airspace is over time—similar to Google Maps “Popular Times”—using ADS-B data. Longer term: distinguish **pattern work** from **through** traffic.

## Status

Run from repo root:

**Collector** (`airpop/`):

- Airports: `airports.json` (lat/lon seed list)
- `uv run poll KVGT` — one-shot aircraft count
- `uv run collect KVGT` — poll every 4 min → `data/KVGT.db`
- `uv run serve KVGT` — live chart at http://127.0.0.1:8000/

**Dev tools** (`airpop/tools/`):

- `uv run sample` — fake 2 weeks of data → `data/sample.db`
- `uv run chart data/KVGT.db` — writes `data/KVGT.html` (static snapshot)

[OpenSky Network](https://opensky-network.org/) — non-commercial use per [OpenSky terms](https://opensky-network.org/about/terms-of-use). 


