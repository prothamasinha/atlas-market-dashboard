# IST 402 — Assignment 4, Part 4.1: Market Data and Dashboard

**Project:** ATLAS — Market Intelligence  
**Student:** Prothama Sinha  
**GitHub repository:** https://github.com/prothamasinha/atlas-market-dashboard  
**Submitted code version (commit):** [`ea1f5ee17ce30ee9ce2e7640e9367a064f951230`](https://github.com/prothamasinha/atlas-market-dashboard/commit/ea1f5ee17ce30ee9ce2e7640e9367a064f951230)  
**Demo video:** https://drive.google.com/file/d/1-RYkLf67IzoSllhk4ALRK_b1kYobiWL9/view?usp=sharing

## Summary

ATLAS is a client-server market monitoring dashboard for the BTC-USD instrument. The FastAPI backend subscribes to Yahoo Finance quotes through `yfinance`, forwards incoming observations to connected browsers over WebSockets, and persists observations in a local SQLite database. The frontend uses TradingView Lightweight Charts to display one-minute price candles and volume estimates. It shows the live quote, its source, source-data age, connection status, and information about stored observations. A retrieval endpoint loads observations from SQLite for historical chart display and replay development.

## Completed work and design decisions

- **Live streaming:** A `yfinance` BTC-USD feed sends quote updates to the FastAPI server; clients receive forwarded `tick` and feed-status messages over the `/ws` WebSocket endpoint.
- **Charts:** The browser aggregates incoming prices into minute-based OHLC candles and visualizes them using Lightweight Charts. The displayed volume is inferred from changes in a reported cumulative day-volume value rather than validated trade-by-trade volume.
- **Data visibility:** The dashboard displays latest price, source name, feed health, source timestamp, receipt timestamp, and source age; it distinguishes live status from connection problems.
- **Persistence:** SQLite stores symbol, observation ID, source time, receipt time, price, raw JSON, cumulative volume, and revision number. The schema includes uniqueness on `(symbol, observation_id, revision)`.
- **Retrieval:** `GET /api/observations` returns stored observations from SQLite. `GET /dashboard` serves the browser interface. The ATLAS dashboard can load historical observations from this API.
- **Structure:** Backend and frontend files are separated; project instructions and architecture notes are maintained in the repository.

## Architecture, database, and startup

**Data flow:** `Yahoo Finance → yfinance → FastAPI → WebSocket (/ws) → browser chart`. In parallel, `FastAPI → SQLite → REST API (/api/observations) → browser historical chart`.

The `market_observations` table records the original source and receipt timestamps, observation identity, version, and payload. A separate `candles` table has fields for OHLC, volume, revision, and `is_complete`, but the current submitted code has not demonstrated complete server-side candle persistence and finalization.

From the GitHub repository root, the local startup procedure is:

```bash
python3 -m pip install fastapi "uvicorn[standard]" yfinance websockets
python3 backend/database.py
python3 -m uvicorn backend.main:app --port 8001
```

Open `http://127.0.0.1:8001/dashboard`. The app is run locally and does not require hard-coded credentials. `.env`, local SQLite databases, and virtual environments are excluded from version control.

## Verification results

| Check | Result |
|---|---|
| Direct Yahoo Finance stream | **Passed:** BTC-USD quote messages appeared in the terminal. |
| FastAPI-to-client WebSocket | **Passed:** `backend/test_ws.py` received a `tick` message. |
| Dashboard visualization | **Passed visually:** live price, minute candles, feed status, and source age were shown. |
| SQLite insert and retrieval | **Passed:** observation count increased; `GET /api/observations` returned an HTTP 200 response and 214 records during one check. |
| Historical chart history | **Observed:** ATLAS subsequently loaded 500 saved records (the API query limit, not necessarily the database total). |
| Replay control | **Implemented in UI, but end-to-end playback not independently verified.** |
| Candle completion/persistence | **Not yet verified end to end.** |
| Duplicate, revision, out-of-order handling | **Partially implemented, not passing all tests:** a SQLite `UNIQUE constraint failed` error was observed when storing a revision. |
| Feed-unavailable condition | **Error/status handling present in backend; controlled demonstration not verified.** |

**Working evidence:** [30–60-second demo video](https://drive.google.com/file/d/1-RYkLf67IzoSllhk4ALRK_b1kYobiWL9/view?usp=sharing); [WebSocket test source](https://github.com/prothamasinha/atlas-market-dashboard/blob/ea1f5ee17ce30ee9ce2e7640e9367a064f951230/backend/test_ws.py); [database implementation](https://github.com/prothamasinha/atlas-market-dashboard/blob/ea1f5ee17ce30ee9ce2e7640e9367a064f951230/backend/database.py); [dashboard source](https://github.com/prothamasinha/atlas-market-dashboard/blob/ea1f5ee17ce30ee9ce2e7640e9367a064f951230/frontend/index.html). The video link must be shared with the instructor as **Anyone with the link → Viewer**.

## Known limitations and remaining work

The availability and update rate of the Yahoo Finance stream depend on the external service. The quotes are not a guaranteed exchange execution feed. Minute candles are assembled in the browser and may be incomplete; the submitted version does not yet demonstrate completed-candle storage and replay of finalized and revised candle states. Volume is approximated from cumulative values. Observation deduplication and revision logic needs a fix for the observed uniqueness error, followed by reproducible duplicate, revised, and out-of-order tests. End-to-end replay and a forced unavailable-feed demonstration remain to be verified. These limitations are disclosed rather than represented as completed functionality.

## Repository documentation

- [README and setup instructions](https://github.com/prothamasinha/atlas-market-dashboard/blob/ea1f5ee17ce30ee9ce2e7640e9367a064f951230/README.md)
- [Agent instructions](https://github.com/prothamasinha/atlas-market-dashboard/blob/ea1f5ee17ce30ee9ce2e7640e9367a064f951230/AGENTS.md)
- [Design and data-flow notes](https://github.com/prothamasinha/atlas-market-dashboard/blob/ea1f5ee17ce30ee9ce2e7640e9367a064f951230/docs/design.md)
- [Full source repository](https://github.com/prothamasinha/atlas-market-dashboard)
- [Exact submitted application-code commit](https://github.com/prothamasinha/atlas-market-dashboard/commit/ea1f5ee17ce30ee9ce2e7640e9367a064f951230)
- [Short demo recording](https://drive.google.com/file/d/1-RYkLf67IzoSllhk4ALRK_b1kYobiWL9/view?usp=sharing)

**Canvas submission:** Upload this `report.md` only. The application source code and supporting documents remain in GitHub.
