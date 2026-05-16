from fastapi import FastAPI, WebSocket
import asyncio
import random
import math

app = FastAPI()

VEHICLE_COUNT = 3
BOUNDS = 12
MAX_SPEED = 0.3

class Vehicle:
    def __init__(self, vehicle_id):
        self.id = vehicle_id
        self.x = random.uniform(-BOUNDS/2, BOUNDS/2)
        self.z = random.uniform(-BOUNDS/2, BOUNDS/2)
        self.angle = random.uniform(0, 2 * math.pi)
        self.speed = random.uniform(0.05, MAX_SPEED)
        self.turn_rate = random.uniform(-0.03, 0.03)

    def update(self):
        self.angle += self.turn_rate * random.uniform(0.8, 1.2)

        self.x += math.cos(self.angle) * self.speed
        self.z += math.sin(self.angle) * self.speed

        if abs(self.x) > BOUNDS / 2:
            self.angle = math.pi - self.angle
            self.x = max(-BOUNDS / 2, min(BOUNDS / 2, self.x))

        if abs(self.z) > BOUNDS / 2:
            self.angle = -self.angle
            self.z = max(-BOUNDS / 2, min(BOUNDS / 2, self.z))

        if random.random() < 0.01:
            self.turn_rate = random.uniform(-0.03, 0.03)

        if random.random() < 0.02:
            self.speed = random.uniform(0.05, MAX_SPEED)

vehicles = [Vehicle(i) for i in range(VEHICLE_COUNT)]

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