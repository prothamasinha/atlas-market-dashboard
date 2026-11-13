# IST 402 — Assignment 4, Part 4.1: Market Data and Dashboard

**Project:** ATLAS — Market Intelligence  
**Student:** [YOUR NAME]  
**GitHub repository:** [PASTE GITHUB REPOSITORY URL]  
**Submitted code commit:** `[PASTE FULL GIT COMMIT HASH]`  
**Demo video (30–60 seconds):** [PASTE ACCESSIBLE VIDEO LINK]

## Summary

ATLAS is a client-server market-monitoring dashboard for BTC-USD. Its Python/FastAPI backend subscribes to streaming quotes from Yahoo Finance using `yfinance`, forwards observations through a WebSocket endpoint, and saves received observations in SQLite. The browser-based frontend uses Lightweight Charts to visualize price action as one-minute candlesticks and provides quote information, source age, and feed status. A retrieval API exposes saved observations for chart history and replay work.

## Completed implementation and key decisions

- **Market data and transport:** Yahoo Finance BTC-USD streaming quote feed; FastAPI backend; browser WebSocket at `/ws`.
- **Visualization:** One-minute OHLC candles assembled from incoming price observations, displayed with TradingView Lightweight Charts; volume display based on changes in cumulative daily volume when available.
- **Freshness and health:** The UI shows latest price, data source (Yahoo Finance), age of the source timestamp, connection state, and source/receipt information.
- **Persistence:** SQLite file `backend/market.db`; backend `save_observation` records source and receipt times, price, identifier, a revision number, and the raw quote payload.
- **Retrieval:** `GET /api/observations` reads stored observations. `GET /dashboard` serves the frontend. The dashboard uses saved observations to populate historical chart data.

## Architecture and database design

`Yahoo Finance -> yfinance WebSocket client -> FastAPI -> /ws -> browser chart`  
`FastAPI -> SQLite market_observations -> GET /api/observations -> browser`.

The `market_observations` table records `observation_id`, `symbol`, `source`, `source_time_ms`, `received_at`, `revision`, `price`, `cumulative_volume`, and `raw_json`, with a uniqueness constraint on (`symbol`, `observation_id`, `revision`). A `candles` table was created with minute timestamps, OHLC, volume, revision, and `is_complete`, but full backend candle persistence/completion has not yet been demonstrated.

For local startup, install `fastapi`, `uvicorn[standard]`, and `yfinance`, then run `python3 backend/database.py` and `python3 -m uvicorn backend.main:app --port 8001`. Open `http://127.0.0.1:8001/dashboard`. No credentials are required in the current local setup; secrets should not be committed to GitHub.

## Verification and evidence

| Test | Result | Evidence to include |
|---|---|---|
| Direct Yahoo Finance subscription for BTC-USD | **Passed** — terminal displayed streaming quotes | [Link to screenshot or video timestamp] |
| Browser WebSocket through FastAPI | **Passed** — `test_ws.py` received a `tick` message | [Link to screenshot or video timestamp] |
| Live dashboard visualization | **Passed visually** — price, candles, live status, and source age were visible | [Link to screenshot or video timestamp] |
| SQLite saving | **Passed** — observations were counted in SQLite | [Link to screenshot or video timestamp] |
| Retrieval API | **Passed** — `/api/observations` returned HTTP 200 and saved observations | [Link to screenshot or video timestamp] |
| Replay behavior | **Not independently verified**; Replay control is displayed | [Add result only after testing] |
| Completed candle persistence | **Not yet verified** | [Add result if completed] |
| Duplicate, revision, out-of-order tests | **Incomplete** — a UNIQUE constraint error was seen during streaming | [Add result if fixed] |
| Unavailable-feed scenario | **Not formally demonstrated**; backend includes an unavailable status path | [Add result if tested] |

The retrieval API was observed returning 214 saved observations at one point, and the redesigned interface later displayed 500 fetched records. The 500 represents the retrieval limit and should not be presented as the total database row count.

## Limitations and next steps

Yahoo Finance's feed availability and update cadence are outside the app's control. The volume calculation from cumulative-day-volume deltas is an approximation, not verified per-trade volume. Candles are currently generated in the browser; backend persistence and completion flags are not fully proven. Replay, feed-failure simulation, and deterministic duplicate/revision/out-of-order tests require final verification. During testing, SQLite produced a `UNIQUE constraint failed` error for observation revisions; this is a known outstanding issue and should not be described as resolved without retesting. If the feed becomes unavailable, recorded observations provide a basis for replay development, but no verified fallback workflow is claimed here.

## Supporting documents and source

- [Project README](README.md)
- [Agent instructions](AGENTS.md)
- [Design notes](docs/design.md)
- [Source repository](PASTE_GITHUB_REPOSITORY_URL)
- [Demonstration video](PASTE_ACCESSIBLE_VIDEO_URL)

**Submission:** Upload only this `report.md` file to Canvas. Source files remain in the linked GitHub repository. The repository and video must be accessible to the instructor.
