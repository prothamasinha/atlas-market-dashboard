
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "market.db"

def init_database():
    conn = sqlite3.connect(DB_PATH)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS market_observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            observation_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            source TEXT NOT NULL,
            source_time_ms INTEGER NOT NULL,
            received_at TEXT NOT NULL,
            revision INTEGER NOT NULL DEFAULT 1,
            price REAL NOT NULL,
            cumulative_volume REAL,
            raw_json TEXT NOT NULL,
            UNIQUE(symbol, observation_id, revision)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS candles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            candle_time INTEGER NOT NULL,
            source_time_ms INTEGER NOT NULL,
            received_at TEXT NOT NULL,
            revision INTEGER NOT NULL DEFAULT 1,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume REAL NOT NULL DEFAULT 0,
            is_complete INTEGER NOT NULL DEFAULT 0,
            UNIQUE(symbol, candle_time, revision)
        )
    """)

    conn.commit()
    conn.close()
    print("SQLite database initialized successfully!")

if __name__ == "__main__":
    init_database()


import json
from datetime import datetime, timezone

def save_observation(tick):
    symbol = tick["id"]
    price = float(tick["price"])
    source_time_ms = int(tick["time"])

    if source_time_ms < 1_000_000_000_000:
        source_time_ms *= 1000

    observation_id = f"{symbol}:{source_time_ms}"
    received_at = datetime.now(timezone.utc).isoformat()
    raw_json = json.dumps(tick, sort_keys=True)

    conn = sqlite3.connect(DB_PATH)

    try:
        previous = conn.execute("""
            SELECT revision, raw_json
            FROM market_observations
            WHERE symbol = ? AND observation_id = ?
            ORDER BY revision DESC
            LIMIT 1
        """, (symbol, observation_id)).fetchone()

        if previous and previous[1] == raw_json:
            return "duplicate"

        revision = previous[0] + 1 if previous else 1

        conn.execute("""
            INSERT INTO market_observations (
                observation_id, symbol, source,
                source_time_ms, received_at, revision,
                price, cumulative_volume, raw_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            observation_id,
            symbol,
            "Yahoo Finance",
            source_time_ms,
            received_at,
            revision,
            price,
            tick.get("day_volume"),
            raw_json
        ))

        conn.commit()
        return "saved"

    finally:
        conn.close()
