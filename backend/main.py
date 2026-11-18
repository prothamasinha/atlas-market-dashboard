
from datetime import datetime, timezone
from fastapi import FastAPI, WebSocket
from backend.database import init_database, save_observation
import yfinance as yf

app = FastAPI(title="Market Dashboard")

# Initialize SQLite database
init_database()

@app.get("/")
def home():
    return {
        "message": "Market Dashboard Backend Running",
        "source": "Yahoo Finance",
        "status": "ready"
    }

@app.websocket("/ws")
async def market_stream(websocket: WebSocket):
    await websocket.accept()

    try:
        await websocket.send_json({
            "type": "status",
            "status": "connecting"
        })

        async with yf.AsyncWebSocket(verbose=False) as yahoo:
            await yahoo.subscribe(["BTC-USD"])

            await websocket.send_json({
                "type": "status",
                "status": "subscribed"
            })

            async def on_message(message):
                # Save observation to SQLite
                db_result = save_observation(message)

                print("Database:", db_result)

                # Forward live observation to dashboard
                await websocket.send_json({
                    "type": "tick",
                    "source": "Yahoo Finance",
                    "received_at": datetime.now(
                        timezone.utc
                    ).isoformat(),
                    "database": db_result,
                    "data": message
                })

            await yahoo.listen(on_message)

    except Exception as e:
        print("Feed unavailable:", str(e))

        try:
            await websocket.send_json({
                "type": "status",
                "status": "unavailable",
                "error": str(e)
            })
            await websocket.close()
        except Exception:
            pass



import sqlite3
import json
from backend.database import DB_PATH

@app.get("/api/observations")
def get_observations():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        rows = conn.execute("""
            SELECT *
            FROM market_observations
            ORDER BY source_time_ms ASC, revision ASC, id ASC
            LIMIT 500
        """).fetchall()

        return {
            "count": len(rows),
            "observations": [
                {
                    "observation_id": row["observation_id"],
                    "symbol": row["symbol"],
                    "source": row["source"],
                    "source_time_ms": row["source_time_ms"],
                    "received_at": row["received_at"],
                    "revision": row["revision"],
                    "price": row["price"],
                    "data": json.loads(row["raw_json"])
                }
                for row in rows
            ]
        }
    finally:
        conn.close()



from pathlib import Path
from fastapi.responses import FileResponse

@app.get("/dashboard")
def show_dashboard():
    frontend_file = (
        Path(__file__).resolve().parent.parent
        / "frontend"
        / "index.html"
    )

    return FileResponse(frontend_file)

from backend.part42_routes import router as part42_router
app.include_router(part42_router)
