# Launch

## Local install

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -U pip setuptools wheel
pip install .
```

## PostgreSQL and Redis via Docker

```powershell
docker compose up -d postgres redis
```

## Bot run

```powershell
.venv\Scripts\Activate.ps1
python run_bot.py
```

## API run

```powershell
.venv\Scripts\Activate.ps1
python run_api.py
```

## Full stack via Docker

```powershell
docker compose up --build
```

## Quick checks

```powershell
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/nodes
```

## Manual Telegram checks

1. Open the bot and send `/start`.
2. Open `Профиль`.
3. Open `Конфиг` and press `Скопировать конфиг`.
4. Press `QR код`.
5. Press `Сменить локацию`.
6. Verify the new config imports into Hiddify.
7. As admin, run `/nodes`.
8. As admin, run `/grant <telegram_id> 1` if you need to activate a user manually.
