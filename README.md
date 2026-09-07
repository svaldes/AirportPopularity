# Airport Popularity

### Welcome! 🙋🏻‍♀️
This repo contains code for a widget that shows traffic levels at a small airport. It can be configured for different airports and ADS-B sources. It can be run locally on your laptop or  [deployed](deploy/README.md).

## Quick Setup

### 0. Prerequisites 

- git
- Python 3.10–3.13
- [uv](https://docs.astral.sh/uv/)

### 1. Install

```bash
git clone https://github.com/svaldes/AirportPopularity.git
cd AirportPopularity
uv sync   # create .venv and install this project + dependencies
```

### 2. Start Data Collection

```bash
export AIRPOP_SOURCE=opensky  # See Data Sources below
uv run collect KVGT
```
### 3. Display Chart

Leave the collector running. In a separate terminal,
```bash
uv run collect KVGT
```
The live data will be served at [http://localhost:8000/](http://localhost:8000/)

## How it Works

```mermaid
flowchart LR
  collector["collect"] --> db["data/ICAO.db"]
  db --> server["serve"]
```

The `collect` process writes traffic counts to a local database every 5 minuntes. `serve` reads the same file and serves the chart.

## Airports

To collect data on a different airport, add an entry to [airports.json](airports.json):
```
"KVNY": {
    "name": "Van Nuys",
    "lat": 34.2098,
    "lon": -118.49,
    "elevation_ft": 802,
    "timezone": "America/Los_Angeles"
  }
```


## Data sources
ADS-B can be collected from one of several sources. OpenSky is free and requires no set-up, so it's a good starting point.

| `AIRPOP_SOURCE` | Notes                                                      |
| --------------- | ---------------------------------------------------------- |
| `opensky`       | Free, non-commercial; often blocked from hyperscaler IPs   |
| `adsbx`         | RapidAPI key (`ADSBX_RAPIDAPI_KEY`, `ADSBX_RAPIDAPI_HOST`) |
| `local`         | Own receiver — coming soon                                     |

### Terms

[OpenSky](https://opensky-network.org/about/terms-of-use) · [ADS-B Exchange AUP](https://www.adsbexchange.com/acceptable-use-policy/)


## Deploy

A public chart needs the collector running continuously (i.e. not on your laptop). To run the collector and server on a VPS, see **[deploy/README.md](deploy/README.md)**.

