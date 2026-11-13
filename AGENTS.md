# Agent Instructions — ATLAS

## Scope
ATLAS is a BTC-USD dashboard built with Python FastAPI, yfinance, browser WebSockets, Lightweight Charts, and SQLite. Preserve the live market stream and database schema when making changes.

## Development rules
- Run the backend from the project root with `python3 -m uvicorn backend.main:app --port 8001`.
- Never commit secrets (`.env`), private tokens, virtual environments, or generated SQLite databases.
- Preserve original source timestamps, receipt timestamps, observation identity, raw payloads, and revisions. Handle duplicate and out-of-order observations deterministically.
- Treat quoted prices and volume as source observations, not necessarily exchange-validated trade prints.
- Make data freshness and unavailable-feed states visible. Do not label replayed data as live.
- Run WebSocket, database, and replay tests before claiming features complete.
