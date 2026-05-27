"""
车辆模拟器 - 模拟视觉模块推送车辆数据
独立运行，通过 WebSocket 向后端推送车辆位置信息
"""
import math
import time
import json
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import websockets


WEBSOCKET_HOST = "127.0.0.1"
WEBSOCKET_PORT = 8000
WEBSOCKET_URL = f"ws://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}/ws/vision"
BOUNDS = 12
PUBLISH_INTERVAL = 0.1  # 每100ms推送一次


def generate_plate(vehicle_id):
    return f"A{vehicle_id:05d}"


class Vehicle:
    def __init__(self, vehicle_id, movement_type="square"):
        self.id = vehicle_id
        self.plate = generate_plate(vehicle_id)
        self.x = 0.0
        self.z = 0.0
        self.angle = 0.0
        self.speed = 0.15
        self.movement_type = movement_type

    def update(self):
        pass

    def to_dict(self):
        return {
            "id": self.id,
            "plate": self.plate,
            "position": [round(self.x, 2), 0.0, round(self.z, 2)],
            "angle": round(self.angle, 2),
            "movement_type": self.movement_type
        }


class SquareVehicle(Vehicle):
    def __init__(self, vehicle_id):
        super().__init__(vehicle_id, "square")
        self.square_size = BOUNDS / 4 - 0.5
        self.corners = [
            (-self.square_size, -self.square_size),
            (self.square_size, -self.square_size),
            (self.square_size, self.square_size),
            (-self.square_size, self.square_size)
        ]
        self.current_corner = 0
        self.x = self.corners[0][0]
        self.z = self.corners[0][1]
        self.speed = 0.15

    def update(self):
        target_x, target_z = self.corners[self.current_corner]
        dx = target_x - self.x
        dz = target_z - self.z
        distance = math.sqrt(dx * dx + dz * dz)

        if distance < 0.1:
            self.current_corner = (self.current_corner + 1) % 4
            return

        self.angle = math.atan2(dz, dx)
        self.x += math.cos(self.angle) * self.speed
        self.z += math.sin(self.angle) * self.speed


class LineVehicle(Vehicle):
    def __init__(self, vehicle_id):
        super().__init__(vehicle_id, "line")
        self.start_x = -BOUNDS / 4 + 1
        self.end_x = BOUNDS / 4 - 1
        self.z = 0.0
        self.x = self.start_x
        self.direction = 1
        self.speed = 0.2

    def update(self):
        self.x += self.direction * self.speed
        if self.x >= self.end_x:
            self.x = self.end_x
            self.direction = -1
        elif self.x <= self.start_x:
            self.x = self.start_x
            self.direction = 1


class CircleVehicle(Vehicle):
    def __init__(self, vehicle_id):
        super().__init__(vehicle_id, "circle")
        self.center_x = 0.0
        self.center_z = 0.0
        self.radius = BOUNDS / 4 - 0.5
        self.angle = 0.0
        self.x = self.center_x + self.radius
        self.z = self.center_z
        self.speed = 0.05

    def update(self):
        self.angle += self.speed
        self.x = self.center_x + math.cos(self.angle) * self.radius
        self.z = self.center_z + math.sin(self.angle) * self.radius


class VehicleSimulator:
    def __init__(self):
        self.vehicles = [
            SquareVehicle(0),
            LineVehicle(1),
            CircleVehicle(2)
        ]
        self._running = False

    async def _connect_and_send(self):
        while self._running:
            try:
                async with websockets.connect(WEBSOCKET_URL, ping_interval=30) as ws:
                    print(f"[WebSocket] 已连接到后端 {WEBSOCKET_URL}")
                    while self._running:
                        for v in self.vehicles:
                            v.update()
                        payload = {
                            "vehicles": [v.to_dict() for v in self.vehicles],
                            "timestamp": time.time()
                        }
                        await ws.send(json.dumps(payload))
                        await asyncio.sleep(PUBLISH_INTERVAL)
            except (Exception, asyncio.CancelledError) as e:
                if isinstance(e, asyncio.CancelledError):
                    print("[WebSocket] 任务被取消")
                    self._running = False
                else:
                    print(f"[WebSocket] 连接错误: {e}")
                    if self._running:
                        await asyncio.sleep(2)

    def start(self):
        if self._running:
            return
        self._running = True
        try:
            asyncio.run(self._connect_and_send())
        except KeyboardInterrupt:
            pass  # 已在 _connect_and_send 中处理

    def stop(self):
        self._running = False


if __name__ == "__main__":
    print("=" * 55)
    print("  车辆模拟器 - WebSocket 推送")
    print("=" * 55)

    simulator = VehicleSimulator()
    simulator.start()

    print(f"\n开始推送 {len(simulator.vehicles)} 辆车数据")
    print(f"目标: {WEBSOCKET_URL}")
    print(f"间隔: {PUBLISH_INTERVAL} 秒\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n停止推送")
        simulator.stop()
