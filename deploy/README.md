# Deploy on a VPS

Paths below assume the repo lives at `/home/ubuntu/AirportPopularity` (Lightsail/Ubuntu). Adjust `User=`, `WorkingDirectory=`, and `ExecStart=` in the unit files if your layout differs.

Files in this directory:

| File | Role |
|------|------|
| `airpop-collect@.service` | systemd template: `collect` for an ICAO |
| `airpop-serve@.service` | systemd template: `serve` on `127.0.0.1:8000` |
| `airpop.env.example` | Copy to `airpop.env` (gitignored) for collector secrets |
| `nginx-airpop.conf` | HTTP reverse proxy to `serve` (TLS later) |

## Collector

```bash
cp deploy/airpop.env.example deploy/airpop.env   # set AIRPOP_SOURCE + keys
sudo cp deploy/airpop-collect@.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now airpop-collect@KPAO
journalctl -u airpop-collect@KPAO -f
```

## Chart + nginx 

`serve` binds localhost; nginx listens on port 80 and reverse-proxies to it.

```bash
sudo cp deploy/airpop-serve@.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now airpop-serve@KPAO

sudo apt update && sudo apt install -y nginx
sudo cp deploy/nginx-airpop.conf /etc/nginx/sites-available/airpop
sudo ln -sf /etc/nginx/sites-available/airpop /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

Browse: `http://PUBLIC_IP/`
