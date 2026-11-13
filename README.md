# ATLAS — Market Intelligence

ATLAS is a student-built BTC-USD financial market dashboard using Yahoo Finance streaming quotes, a FastAPI WebSocket backend, SQLite storage, and a browser candlestick chart.

## Local setup
From the repository root:

```bash
python3 -m pip install fastapi "uvicorn[standard]" yfinance websockets
python3 backend/database.py
python3 -m uvicorn backend.main:app --port 8001
```

Then open `http://127.0.0.1:8001/dashboard`.

## Key routes
- `/` — backend health/startup response
- `/ws` — browser WebSocket stream for market observations and feed status
- `/api/observations` — JSON retrieval of saved observations
- `/dashboard` — browser market dashboard

## Architecture
Yahoo Finance → yfinance → FastAPI → WebSockets → chart; FastAPI → SQLite → retrieval API → chart history.

## Validation
The live quote stream, client WebSocket, local database writes, and retrieval endpoint were observed working. Do not claim full compliance with replay, completed-candle persistence, duplicate/revision/out-of-order tests or feed-failure testing without additional verification. See [design notes](docs/design.md) and [agent instructions](AGENTS.md).

## Safety and limitations
This is an educational market visualization, not a trading or investment system. Quotes and displayed volume may be delayed, incomplete or revised; not suitable for order execution. Keep `.env`, virtual environments and database files out of public Git repositories.
