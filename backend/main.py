from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketDisconnect
import asyncio

from vehicle_simulation import vehicles
from db import get_connection
from methane_simulation import methane_sensors, update_all_sensors, get_alerts

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
    conn.close()
    return JSONResponse({"vehicles": [{"id": r[0], "plate": r[1]} for r in rows]})


@app.get("/api/vehicles/{vehicle_id}")
async def get_vehicle(vehicle_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, plate FROM vehicles WHERE id = ?", (vehicle_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return JSONResponse({"id": row[0], "plate": row[1]})
    return JSONResponse({"error": "Vehicle not found"}, status_code=404)


@app.get("/api/methane")
async def get_methane():
    return JSONResponse({
        "methane": [sensor.get_data() for sensor in methane_sensors]
    })


@app.get("/api/methane/{sensor_id}")
async def get_methane(sensor_id: int):
    if sensor_id < 0 or sensor_id >= len(methane_sensors):
        return JSONResponse({"error": "Sensor not found"}, status_code=404)
    return JSONResponse(methane_sensors[sensor_id].get_data())


@app.post("/api/methane/{sensor_id}/update")
async def update_methane(sensor_id: int):
    if sensor_id < 0 or sensor_id >= len(methane_sensors):
        return JSONResponse({"error": "Sensor not found"}, status_code=404)
    methane_sensors[sensor_id].update()
    return JSONResponse(methane_sensors[sensor_id].get_data())


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()

    while True:
        try:
            for v in vehicles:
                v.update()

            new_alerts = update_all_sensors()

            data = {
                "objects": [
                    {
                        "id": v.id,
                        "type": "vehicle",
                        "position": [round(v.x, 2), 0.0, round(v.z, 2)]
                    }
                    for v in vehicles
                ],
                "alerts": get_alerts(),
                "methane": [s.get_data() for s in methane_sensors]
            }
            await websocket.send_json(data)
            await asyncio.sleep(0.1)
        except WebSocketDisconnect:
            break


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)