# Telegram VPN Service MVP

MVP Telegram VPN service on Python 3.12, aiogram 3, PostgreSQL, Redis, Xray Reality, and 3x-ui.

## What is already wired

- Telegram bot with menu, profile, config, QR, location switch, support, and top-up placeholder
- PostgreSQL models and auto schema bootstrap
- Redis config placeholder
- Xray / 3x-ui panel client
- VPN config issuance per location
- client create / update / delete lifecycle in 3x-ui
- basic admin flows: stats, nodes, ticket replies, manual subscription grant, VPN reset
- FastAPI health and node summary endpoints

## Main files

- [run_bot.py](</I:/vpnn/run_bot.py>)
- [run_api.py](</I:/vpnn/run_api.py>)
- [docker-compose.yml](</I:/vpnn/docker-compose.yml>)
- [.env](</I:/vpnn/.env>)
- [docs/launch.md](</I:/vpnn/docs/launch.md>)

## Quick start

### Full stack in Docker

```powershell
docker compose up --build
```

### Local bot run

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -U pip setuptools wheel
pip install .
docker compose up -d postgres redis
python run_bot.py
```

### Local API run

```powershell
.venv\Scripts\Activate.ps1
python run_api.py
```

### Checks

```powershell
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/nodes
```

## Admin helper commands

- `/admin`
- `/nodes`
- `/grant <telegram_id> <months>`
- `/vpnreset <telegram_id>`
