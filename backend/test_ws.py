
import asyncio
import json
import websockets

async def main():
    print("Connecting to market dashboard...")

    async with websockets.connect(
        "ws://127.0.0.1:8000/ws"
    ) as socket:

        for _ in range(10):
            try:
                message = await asyncio.wait_for(
                    socket.recv(), timeout=30
                )
            except asyncio.TimeoutError:
                print("No update received in 30 seconds.")
                break

            data = json.loads(message)
            print("Received:", data)

            if data.get("type") == "tick":
                print("SUCCESS! Live market data received!")
                break

asyncio.run(main())
