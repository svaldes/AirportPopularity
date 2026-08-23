# Airport Popularity

Estimate how busy a small airport’s airspace is over time—similar to Google Maps “Popular Times”—using ADS-B data. Longer term: distinguish **pattern work** from **through** traffic.

## Status

Run from repo root:

**Collector** (`airpop/`):

- Airports: `airports.json` (lat/lon seed list)
- `uv run poll KVGT` — one-shot aircraft count
- `uv run collect KVGT` — poll every 5 min → `data/KVGT.db`
- `uv run serve KVGT` — live chart at http://127.0.0.1:8000/
- `uv run serve KVGT --host 0.0.0.0` — bind all interfaces (open the port in the VPS firewall)

**Dev tools** (`airpop/tools/`):

- `uv run sample` — fake 2 weeks of data → `data/sample.db`
- `uv run chart data/KVGT.db` — writes `data/KVGT.html` (static snapshot)

## Data sources

ADS-B data can come from one of several sources. **`AIRPOP_SOURCE` must be set** in the environment.

| `AIRPOP_SOURCE` | Meaning |
|-----------------|--------|
| `opensky` | [OpenSky Network](https://opensky-network.org/) — free, non-commercial |
| `adsbx` | [ADS-B Exchange](https://www.adsbexchange.com/) Paid API via RapidAPI; Compatible with Lightsail/AWS |
| `local` | Your own receiver (e.g. tar1090 / readsb JSON) — planned |

Example for `adsbx`:

```bash
export AIRPOP_SOURCE=adsbx
export ADSBX_RAPIDAPI_KEY=...
export ADSBX_RAPIDAPI_HOST=adsbexchange-com1.p.rapidapi.com
uv run poll KVGT
```

Each deployer runs their own collector with their own credentials.

## VPS collector (systemd)

On the server (paths assume clone at `~/AirportPopularity`):

```bash
cp deploy/airpop.env.example deploy/airpop.env   # edit secrets
sudo cp deploy/airpop-collect@.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now airpop-collect@KPAO   # ICAO after @
sudo systemctl status airpop-collect@KPAO
```

Logs: `journalctl -u airpop-collect@KPAO -f`

**Terms:** [OpenSky](https://opensky-network.org/about/terms-of-use) · [ADS-B Exchange AUP](https://www.adsbexchange.com/acceptable-use-policy/)
