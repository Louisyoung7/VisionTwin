from fastapi import FastAPI, WebSocket
import asyncio

from data_generator import vehicles

app = FastAPI()

@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.receive_text()

    while True:
        for v in vehicles:
            v.update()

        data = {
            "objects": [
                {
                    "id": v.id,
                    "type": "vehicle",
                    "position": [round(v.x, 2), 0.0, round(v.z, 2)]
                }
                for v in vehicles
            ]
        }
        await websocket.send_json(data)
        await asyncio.sleep(0.1)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)