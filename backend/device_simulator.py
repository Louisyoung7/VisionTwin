"""
设备模拟器 - 模拟下位机推送 MQTT 数据
独立运行，连接到本地 EMQX broker
"""
import random
import time
import json
import sys
import os

# 添加 backend 目录到 path，以便导入 mqtt_client
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mqtt_client import MQTTClient


SENSOR_COUNT = 5
BOUNDS = 12
MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_PREFIX = "devices/methane"
PUBLISH_INTERVAL = 1.0


class MethaneSimulator:
    """甲烷传感器模拟器"""

    def __init__(self):
        self.client = MQTTClient(
            client_id=f"methane_simulator_{int(time.time())}",
            host=MQTT_HOST,
            port=MQTT_PORT
        )
        # 初始甲烷值 0~25%
        self.sensors = [
            {
                "id": i,
                "location_x": round(random.uniform(-BOUNDS/2, BOUNDS/2), 2),
                "location_z": round(random.uniform(-BOUNDS/2, BOUNDS/2), 2),
                "methane_percentage": round(random.uniform(0.0, 25.0), 2)
            }
            for i in range(SENSOR_COUNT)
        ]

    def connect(self) -> bool:
        print(f"正在连接 MQTT broker {MQTT_HOST}:{MQTT_PORT}...")
        if self.client.connect(timeout=5.0):
            print("连接成功")
            return True
        print("连接失败")
        return False

    def disconnect(self):
        self.client.disconnect()
        print("已断开连接")

    def _update_sensors(self):
        """更新所有传感器数据"""
        for sensor in self.sensors:
            # 随机波动 ±5
            sensor["methane_percentage"] += random.uniform(-5.0, 5.0)
            sensor["methane_percentage"] = round(
                max(0.0, min(100.0, sensor["methane_percentage"])), 2
            )

    def publish_all(self):
        """发布所有传感器数据"""
        self._update_sensors()
        for sensor in self.sensors:
            topic = f"{MQTT_TOPIC_PREFIX}/{sensor['id']}/data"
            payload = {
                "id": sensor["id"],
                "location": [sensor["location_x"], 0.0, sensor["location_z"]],
                "methane_percentage": sensor["methane_percentage"],
                "timestamp": time.time()
            }
            self.client.publish(topic, payload, qos=1)
        return self.sensors

    def run(self):
        """主循环"""
        if not self.connect():
            return

        print(f"\n开始推送 {SENSOR_COUNT} 个甲烷传感器数据")
        print(f"主题: {MQTT_TOPIC_PREFIX}/<id>/data")
        print(f"间隔: {PUBLISH_INTERVAL} 秒")
        print(f"EMQX WebSocket 端口: 8083 (可选)\n")

        count = 0
        try:
            while True:
                sensors = self.publish_all()
                count += 1
                # 简洁输出：只显示 id 和 值
                values = " ".join([f"#{s['id']}:{s['methane_percentage']}%" for s in sensors])
                print(f"[{count:03d}] {values}")
                time.sleep(PUBLISH_INTERVAL)
        except KeyboardInterrupt:
            print("\n\n停止推送")
        finally:
            self.disconnect()


if __name__ == "__main__":
    print("=" * 55)
    print("  甲烷传感器模拟器 - MQTT 推送")
    print("=" * 55)

    simulator = MethaneSimulator()
    simulator.run()
