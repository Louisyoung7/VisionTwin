"""
视觉模块模拟器 - 独立进程运行
模拟 C4_stream 推送车辆检测数据，通过 WebSocket 发送实时坐标和路径合规状态

用法:
  python vision_simulator.py                        # 默认1秒间隔，3辆车
  python vision_simulator.py --interval 0.5         # 0.5秒间隔
  python vision_simulator.py --vehicles 5           # 5辆车
  python vision_simulator.py --violation-rate 0.3   # 30%违规概率
  python vision_simulator.py --host 192.168.1.100   # 指定后端地址
"""
import argparse
import asyncio
import json
import random
import signal
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import SERVER_HOST, SERVER_PORT

try:
    import websockets
except ImportError:
    print("需要安装 websockets 库: pip install websockets")
    exit(1)


PLATES = [
    "京A12345", "京B67890", "沪A11111", "沪B22222",
    "粤A33333", "粤B44444", "苏A55555", "苏B66666",
    "浙A77777", "浙B88888",
]

# 规划路线：zone 1→2→3→4
ROUTE_ZONES = [1, 2, 3, 4]

# SVG 像素空间 (floot.svg: 502x636)
# 路线: 左→上→右→下，四个区域对应 floor plan 上的四个位置
ZONE_COORDS = {
    1: (40, 140, 350, 480),   # 左区
    2: (180, 320, 60, 200),   # 上区
    3: (360, 460, 350, 480),  # 右区
    4: (180, 320, 440, 580),  # 下区（出口）
}

VIOLATION_TYPES = [
    {"type": "unplanned_zone", "description": "闯入未规划区域"},
    {"type": "wrong_order", "description": "区域顺序错误"},
    {"type": "missed_zone", "description": "遗漏必经区域"},
    {"type": "stagnation", "description": "在区域内逗留过久"},
]


class SimVehicle:
    def __init__(self, track_id: int, plate: str, violation_rate: float = 0.2):
        self.track_id = track_id
        self.plate = plate
        self.violation_rate = violation_rate
        self.active = True

        # 路线状态
        self.visited_zones: list[int] = []
        self.current_zone_idx = 0
        self.is_violating = False
        self.violations: list[dict] = []

        # 坐标
        self.x = 0.0
        self.y = 0.0
        self._init_position()

        # 模拟生命周期
        self._lifetime_frames = random.randint(60, 200)
        self._frame_count = 0

    def _init_position(self):
        zone = ROUTE_ZONES[0]
        coords = ZONE_COORDS[zone]
        self.x = random.uniform(coords[0], coords[1])
        self.y = random.uniform(coords[2], coords[3])
        self.visited_zones = [zone]
        self.current_zone_idx = 0

    def step(self):
        self._frame_count += 1

        # 生命周期结束 → 车辆消失
        if self._frame_count >= self._lifetime_frames:
            self.active = False
            return

        # 决定是否进入下一个 zone
        if self.current_zone_idx < len(ROUTE_ZONES) - 1:
            # 80% 概率正常前进，20% 概率停留
            if random.random() < 0.8:
                self.current_zone_idx += 1
                new_zone = ROUTE_ZONES[self.current_zone_idx]
                self.visited_zones.append(new_zone)

                # 坐标跳到新 zone
                coords = ZONE_COORDS[new_zone]
                self.x = random.uniform(coords[0], coords[1])
                self.y = random.uniform(coords[2], coords[3])

        # 在当前 zone 内微移
        coords = ZONE_COORDS[ROUTE_ZONES[self.current_zone_idx]]
        self.x += random.uniform(-10, 10)
        self.y += random.uniform(-10, 10)
        self.x = max(coords[0], min(coords[1], self.x))
        self.y = max(coords[2], min(coords[3], self.y))

        # 违规判定
        self.is_violating = False
        self.violations = []
        if random.random() < self.violation_rate:
            self.is_violating = True
            self.violations = [random.choice(VIOLATION_TYPES).copy()]
            # 补充 zone 信息
            self.violations[0]["zone"] = ROUTE_ZONES[self.current_zone_idx]

    def to_dict(self) -> dict:
        current_zone = ROUTE_ZONES[self.current_zone_idx]
        expected_zone = ROUTE_ZONES[min(self.current_zone_idx + 1, len(ROUTE_ZONES) - 1)]
        progress = f"{self.current_zone_idx + 1}/{len(ROUTE_ZONES)}"

        compliance_status = "violation" if self.is_violating else "compliant"

        return {
            "track_id": self.track_id,
            "class_name": "car",
            "confidence": round(random.uniform(0.75, 0.98), 2),
            "bbox": [
                int(self.x - 40),
                int(self.y - 25),
                80,
                50
            ],
            "center": [round(self.x, 1), round(self.y, 1)],
            "plate_number": self.plate,
            "current_zones": [current_zone],
            "path_compliance": {
                "status": compliance_status,
                "expected_zone": expected_zone,
                "visited_zones": self.visited_zones[:],
                "progress": progress,
                "violations": self.violations[:]
            }
        }


class VisionSimulator:
    def __init__(self, interval=1.0, host="127.0.0.1", port=8000,
                 num_vehicles=3, violation_rate=0.2):
        self.interval = interval
        self.host = host
        self.port = port
        self.num_vehicles = num_vehicles
        self.violation_rate = violation_rate
        self.frame_idx = 0
        self.running = False
        self.vehicles: list[SimVehicle] = []
        self._next_track_id = 1

    def _spawn_vehicle(self) -> SimVehicle:
        plate = random.choice(PLATES)
        v = SimVehicle(self._next_track_id, plate, self.violation_rate)
        self._next_track_id += 1
        return v

    def _ensure_vehicles(self):
        # 移除失活车辆
        self.vehicles = [v for v in self.vehicles if v.active]
        # 补充新车辆
        while len(self.vehicles) < self.num_vehicles:
            self.vehicles.append(self._spawn_vehicle())

    async def run(self):
        self.running = True
        ws_url = f"ws://{self.host}:{self.port}/ws/vision"

        print("=" * 45)
        print("  视觉模块模拟器")
        print(f"  间隔: {self.interval}s")
        print(f"  后端: {ws_url}")
        print(f"  车辆数: {self.num_vehicles}")
        print(f"  违规概率: {self.violation_rate * 100:.0f}%")
        print("=" * 45)
        print("\n按 Ctrl+C 停止\n")

        try:
            async with websockets.connect(ws_url) as ws:
                print("[WebSocket] 已连接\n")

                while self.running:
                    self.frame_idx += 1
                    self._ensure_vehicles()

                    # 推进所有车辆状态
                    for v in self.vehicles:
                        v.step()

                    # 移除失活
                    self.vehicles = [v for v in self.vehicles if v.active]

                    # 构建帧数据
                    frame_data = {
                        "type": "vehicle_detect",
                        "timestamp": datetime.now().isoformat(timespec="milliseconds"),
                        "frame_idx": self.frame_idx,
                        "camera_id": "192.168.31.201",
                        "vehicle_count": len(self.vehicles),
                        "vehicles": [v.to_dict() for v in self.vehicles]
                    }

                    await ws.send(json.dumps(frame_data))

                    # 打印摘要
                    parts = []
                    for v in self.vehicles:
                        status = "✗违规" if v.is_violating else "✓合规"
                        zone = ROUTE_ZONES[v.current_zone_idx]
                        parts.append(f"{v.plate} zone={zone} {status}")
                    print(f"[帧#{self.frame_idx}] {len(self.vehicles)}辆 | {' | '.join(parts)}")

                    await asyncio.sleep(self.interval)

        except ConnectionRefusedError:
            print("[错误] 无法连接后端，请确认后端已启动")
        except Exception as e:
            print(f"[错误] {e}")

        print("[停止] 模拟器已退出")

    def stop(self):
        self.running = False


def main():
    parser = argparse.ArgumentParser(description="视觉模块模拟器")
    parser.add_argument("--interval", type=float, default=1.0,
                        help="帧间隔秒数 (默认: 1.0)")
    parser.add_argument("--host", default=SERVER_HOST,
                        help=f"后端地址 (默认: {SERVER_HOST})")
    parser.add_argument("--port", type=int, default=SERVER_PORT,
                        help=f"后端端口 (默认: {SERVER_PORT})")
    parser.add_argument("--vehicles", type=int, default=3,
                        help="同时在线车辆数 (默认: 3)")
    parser.add_argument("--violation-rate", type=float, default=0.2,
                        help="违规概率 0~1 (默认: 0.2)")
    args = parser.parse_args()

    sim = VisionSimulator(
        interval=args.interval,
        host=args.host,
        port=args.port,
        num_vehicles=args.vehicles,
        violation_rate=args.violation_rate,
    )

    signal.signal(signal.SIGINT, lambda *_: sim.stop())
    signal.signal(signal.SIGTERM, lambda *_: sim.stop())

    asyncio.run(sim.run())


if __name__ == "__main__":
    main()