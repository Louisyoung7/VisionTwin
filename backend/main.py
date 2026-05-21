from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from data_generator import vehicles
from database import get_connection

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/vehicles")
async def get_vehicles():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, plate FROM vehicles")
    rows = cursor.fetchall()
    return JSONResponse({"vehicles": [{"id": r[0], "plate": r[1]} for r in rows]})


@app.get("/api/vehicles/{vehicle_id}")
async def get_vehicle(vehicle_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, plate FROM vehicles WHERE id = ?", (vehicle_id,))
    row = cursor.fetchone()
    if row:
        return JSONResponse({"id": row[0], "plate": row[1]})
    return JSONResponse({"error": "Vehicle not found"}, status_code=404)


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