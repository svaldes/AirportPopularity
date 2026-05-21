# Airport Popularity

Estimate how busy a small airport’s airspace is over time—similar to Google Maps “Popular Times”—using ADS-B data. Longer term: distinguish **pattern work** from **through** traffic.

## Status

Run from repo root:

**Collector** (`airpop/`):

- `uv run poll` — one-shot aircraft count
- `uv run collect` — poll every 4 min → `data/airport.db`

**Dev tools** (`airpop/tools/`):

- `uv run sample` — fake 2 weeks of data → `data/sample.db`
- `uv run chart data/airport.db` — writes `data/airport.html`

[OpenSky Network](https://opensky-network.org/) — non-commercial use per [OpenSky terms](https://opensky-network.org/about/terms-of-use). 


