"""
MQTT Broker 封装 - 处理甲烷传感器数据订阅和随机指令发布
"""
import json
import random
import time
import threading
from mqtt_client import MQTTClient


NUM_DEVICES = 4
DEVICE_IDS = ["A", "B", "C", "D"]
WARNING_THRESHOLD = 40.0
DANGER_THRESHOLD = 70.0
DIRECTION_MAP = {1: "左转", 2: "右转", 3: "直行"}  # 1=左转, 2=右转, 3=直行，仅供日志显示
_mqtt_publisher: MQTTClient | None = None
_mqtt_publisher_lock = threading.Lock()
mqtt_sensors: dict[int, dict] = {}
mqtt_sensors_lock = threading.Lock()


def _get_mqtt_publisher() -> MQTTClient:
    global _mqtt_publisher
    with _mqtt_publisher_lock:
        if _mqtt_publisher is None:
            _mqtt_publisher = MQTTClient(
                client_id=f"backend_publisher_{int(time.time())}",
                host="localhost",
                port=1883
            )
            _mqtt_publisher.connect(timeout=3.0)
    return _mqtt_publisher


def _on_methane_message(topic: str, payload: bytes):
    from alerts import check_and_generate_alert
    try:
        data = json.loads(payload.decode("utf-8"))
        sensor_id = data.get("id")
        if sensor_id is None:
            return

        methane_pct = data.get("methane_percentage", 0)
        location = data.get("location", [0, 0, 0])

        old_pct = mqtt_sensors.get(sensor_id, {}).get("methane_percentage", 0)

        with mqtt_sensors_lock:
            mqtt_sensors[sensor_id] = {
                "id": sensor_id,
                "location": location,
                "methane_percentage": round(methane_pct, 2),
                "last_update": time.time()
            }

        if old_pct < DANGER_THRESHOLD <= methane_pct:
            check_and_generate_alert(sensor_id, "danger", methane_pct, location)
        elif old_pct < WARNING_THRESHOLD <= methane_pct < DANGER_THRESHOLD:
            check_and_generate_alert(sensor_id, "warning", methane_pct, location)

    except Exception as e:
        print(f"[MQTT] 解析甲烷数据失败: {e}")


def _start_mqtt_subscriber():
    client = MQTTClient(
        client_id=f"backend_subscriber_{int(time.time())}",
        host="localhost",
        port=1883
    )

    def on_connect(c, ud, flags, rc):
        if rc == 0:
            print("[MQTT] 后端订阅者已连接")
            c.subscribe("devices/methane/+/data", 1)

    def on_message(c, ud, msg):
        _on_methane_message(msg.topic, msg.payload)

    def on_disconnect(c, ud, rc):
        print(f"[MQTT] 后端订阅者断开连接: rc={rc}")

    client._client.on_connect = on_connect
    client._client.on_message = on_message
    client._client.on_disconnect = on_disconnect

    if client.connect(timeout=5.0):
        client._client.loop_start()
        print("[MQTT] 后端订阅者已启动")


def _start_random_publisher():
    """后台线程：每 3~8 秒随机向 4 个下位机发布指令"""
    def run():
        while True:
            try:
                publisher = _get_mqtt_publisher()
                idx = random.randint(0, NUM_DEVICES - 1)
                device_id = DEVICE_IDS[idx]
                command = random.choice([1, 1, 2, 2, 3])
                direction = DIRECTION_MAP[command]

                payload = {device_id: str(command)}
                topic = f"device/A{device_id}/command"
                publisher.publish(topic, payload, qos=1)
                print(f"[MQTT 发布] 设备 {device_id} {direction} (command={command}) → {topic}")
            except Exception as e:
                print(f"[MQTT 发布失败] {e}")

            time.sleep(random.uniform(3.0, 8.0))

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    print(f"[MQTT] 随机发布者已启动，共 {NUM_DEVICES} 个下位机")


def publish_device_command(device_id: str, command: int):
    """供 API 调用，向指定下位机发送指令"""
    direction = DIRECTION_MAP.get(command, "未知")
    publisher = _get_mqtt_publisher()
    payload = {device_id: str(command)}
    topic = f"device/{device_id}/command"
    publisher.publish(topic, payload, qos=1)
    return direction, topic


def start():
    """启动所有 MQTT 相关后台线程"""
    sub_thread = threading.Thread(target=_start_mqtt_subscriber, daemon=True)
    sub_thread.start()
    _start_random_publisher()
