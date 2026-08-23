# Airport Popularity

Estimate how busy a small airport’s airspace is over time using ADS-B data. 

## Run locally

From repo root (`AIRPOP_SOURCE` required):

| Command | What it does |
|---------|----------------|
| `uv run poll KVGT` | One-shot aircraft count |
| `uv run collect KVGT` | Poll every 5 min → `data/KVGT.db` |
| `uv run serve KVGT` | Chart at http://127.0.0.1:8000/ |
| `uv run sample` | Fake data → `data/sample.db` |
| `uv run chart data/KVGT.db` | Static HTML snapshot |

Airports: `airports.json`.

## Data sources

| `AIRPOP_SOURCE` | Notes |
|-----------------|--------|
| `opensky` | Free, non-commercial; often blocked from hyperscaler IPs |
| `adsbx` | RapidAPI key (`ADSBX_RAPIDAPI_KEY`, `ADSBX_RAPIDAPI_HOST`) |
| `local` | Own receiver — planned |

Each deployer runs their own collector with their own credentials.

## Deploy

VPS setup: **[deploy/README.md](deploy/README.md)**.

## Terms

[OpenSky](https://opensky-network.org/about/terms-of-use) · [ADS-B Exchange AUP](https://www.adsbexchange.com/acceptable-use-policy/)
