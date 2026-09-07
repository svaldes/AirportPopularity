# Deploy on a VPS

Paths below assume the repo lives at `/home/ubuntu/AirportPopularity` (Lightsail/Ubuntu). Adjust `User=`, `WorkingDirectory=`, and `ExecStart=` in the unit files if your layout differs.

| File | Role |
|------|------|
| `airpop-collect@.service` | systemd template: `collect` for an ICAO |
| `airpop-serve@.service` | systemd template: `serve` on `127.0.0.1:8000` |
| `airpop.env.example` | Copy to `airpop.env` (gitignored) for collector secrets |
| `nginx-airpop.conf` | nginx reverse proxy to `serve` |

## Collector

```bash
cp deploy/airpop.env.example deploy/airpop.env   # set AIRPOP_SOURCE + keys
sudo cp deploy/airpop-collect@.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now airpop-collect@KPAO
journalctl -u airpop-collect@KPAO -f
```

## Chart + nginx (HTTP)

`serve` on localhost:8000; nginx on :80 reverse-proxies to it. Edit `server_name` in the nginx config to your hostname.

```bash
sudo cp deploy/airpop-serve@.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now airpop-serve@KPAO

sudo apt update && sudo apt install -y nginx
sudo cp deploy/nginx-airpop.conf /etc/nginx/sites-available/airpop
# edit server_name in that file
sudo ln -sf /etc/nginx/sites-available/airpop /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

Firewall: TCP **80** (and **443** once you enable TLS).

## TLS (certbot)

DNS A record must already point at this host. Then:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d airpop.example.com
```

Certbot rewrites the nginx site for TLS termination and renews via systemd timer.


## Embed

Iframe the live chart with `?embed=1`:

```html
<iframe src="https://your-host/?embed=1" title="KVGT traffic"></iframe>
```
