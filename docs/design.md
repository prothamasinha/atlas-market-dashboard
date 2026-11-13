# ATLAS — Design Notes (Assignment 4.1)

## Data flow
1. `yfinance` subscribes to Yahoo Finance BTC-USD market messages.
2. FastAPI receives each quote, records its receipt time, and calls the SQLite persistence function.
3. FastAPI sends quote/status JSON to browser clients using `/ws`.
4. Lightweight Charts displays the price observations as one-minute OHLC candlesticks with a volume histogram.
5. `GET /api/observations` serves saved records in ascending source-time order for history and replay.

## SQLite schema
- `market_observations`: `id`, `observation_id`, `symbol`, `source`, `source_time_ms`, `received_at`, `revision`, `price`, `cumulative_volume`, `raw_json`; unique (`symbol`, `observation_id`, `revision`).
- `candles`: `id`, `symbol`, `candle_time`, `source_time_ms`, `received_at`, `revision`, `open`, `high`, `low`, `close`, `volume`, `is_complete`; unique (`symbol`, `candle_time`, `revision`).

## Architectural decisions
- SQLite is local, simple and adequate for a class demonstration. It is not a multi-user production market datastore.
- Time is stored in UTC or epoch timestamps; browser converts for display.
- The frontend chart currently builds candles from observed price events; backend candle storage is not yet verified.
- Volume estimated from nonnegative differences in reported cumulative daily volume can differ from trade-by-trade volume.

## Known test gap
During streaming, the current `save_observation` path has produced a SQLite uniqueness conflict, so idempotence/revision behavior needs deterministic tests and correction before being described as complete. The unavailable-feed condition and replay functionality also need explicit evidence.
