# Airport Popularity

Estimate how busy a small airport’s airspace is over time—similar to Google Maps “Popular Times”—using ADS-B data. Longer term: distinguish **pattern work** from **through** traffic.

## Status

Run from repo root (creates `data/airport.db`):

- `uv run collect` — poll every 4 min, log to SQLite `poll_samples`

[OpenSky Network](https://opensky-network.org/) — non-commercial use per [OpenSky terms](https://opensky-network.org/about/terms-of-use). 


