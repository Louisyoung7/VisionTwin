"""
MQTT Broker 封装 - 处理甲烷传感器数据订阅和指令发布
"""
import json
import time
import threading
from mqtt_client import MQTTClient
from config import MQTT_HOST, MQTT_PORT, LOG_METHANE_SENSOR


NUM_DEVICES = 4
DEVICE_IDS = ["A", "B", "C", "D"]
WARNING_THRESHOLD = 0.0
DANGER_THRESHOLD = 5.0
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
                host=MQTT_HOST,
                port=MQTT_PORT
            )
            _mqtt_publisher.connect(timeout=3.0)
    return _mqtt_publisher


def _on_methane_message(topic: str, payload: bytes):
    from alerts import check_and_generate_alert
    from db import save_methane_history
    from ws_endpoints import broadcast_alert_sync, broadcast_methane_sensor
    try:
        data = json.loads(payload.decode("utf-8"))
        sensor_id = data.get("id")
        if sensor_id is None:
            return

        methane_pct = data.get("methane_percentage", 0)
        location = data.get("location", [0, 0, 0])

        alert_triggered = None
        with mqtt_sensors_lock:
            old_pct = mqtt_sensors.get(sensor_id, {}).get("methane_percentage", 0)
            mqtt_sensors[sensor_id] = {
                "id": sensor_id,
                "location": location,
                "methane_percentage": round(methane_pct, 2),
                "last_update": time.time()
            }

            # 保存甲烷历史记录
            save_methane_history(sensor_id, methane_pct, location)

            # 打印气体传感器日志
            if LOG_METHANE_SENSOR:
                print(f"[甲烷传感器] ID={sensor_id} 甲烷={methane_pct:.2f}% 位置={location}")

            alert_triggered = None
            if old_pct < DANGER_THRESHOLD <= methane_pct:
                alert_triggered = "danger"
                alert = check_and_generate_alert(sensor_id, "danger", methane_pct, location)
                if alert:
                    broadcast_alert_sync(alert)
            elif old_pct < WARNING_THRESHOLD <= methane_pct < DANGER_THRESHOLD:
                alert_triggered = "warning"
                alert = check_and_generate_alert(sensor_id, "warning", methane_pct, location)
                if alert:
                    broadcast_alert_sync(alert)

            # 广播传感器数据
            broadcast_methane_sensor(sensor_id, methane_pct, location, alert_triggered)

    except Exception:
            import traceback
            traceback.print_exc()


def _on_docked_vehicle_message(topic: str, payload: bytes):
    """处理停靠车辆车牌号数据"""
    from db import save_docked_vehicle
    try:
        data = json.loads(payload.decode("utf-8"))
        plate = data.get("plate")
        if plate is None:
            return

        save_docked_vehicle(plate)

    except Exception:
            import traceback
            traceback.print_exc()


def _start_mqtt_subscriber():
    client = MQTTClient(
        client_id=f"backend_subscriber_{int(time.time())}",
        host=MQTT_HOST,
        port=MQTT_PORT
    )

    def on_connect(c, ud, flags, rc):
        if rc == 0:
            client._connect_event.set()
            c.subscribe("devices/methane/+/data", 1)
            c.subscribe("devices/docked/+/plate", 1)
        else:
            print(f"MQTT subscriber connect failed, rc={rc}")

    def on_message(c, ud, msg):
        if msg.topic.startswith("devices/docked/"):
            _on_docked_vehicle_message(msg.topic, msg.payload)
        else:
            _on_methane_message(msg.topic, msg.payload)

    def on_disconnect(c, ud, rc):
        pass

    client._client.on_connect = on_connect
    client._client.on_message = on_message
    client._client.on_disconnect = on_disconnect

    if client.connect(timeout=5.0):
        client._client.loop_start()
    else:
        print("MQTT subscriber 启动失败，甲烷传感器功能将不可用")


def _start_mqtt_publisher():
    """后台线程：每 5 秒向各下位机发布固定指令（A右转, B右转, C/D直行）"""
    # 固定指令映射: A=右转(2), B=右转(2), C=直行(3), D=直行(3)
    DEVICE_COMMANDS = {
        "A": 2,  # 右转
        "B": 2,  # 右转
        "C": 3,  # 直行
        "D": 3   # 直行
    }

    def run():
        while True:
            try:
                publisher = _get_mqtt_publisher()
                for device_id, command in DEVICE_COMMANDS.items():
                    payload = {device_id: str(command)}
                    topic = f"devices/{device_id}/command"
                    publisher.publish(topic, payload, qos=1)
            except Exception:
                import traceback
                traceback.print_exc()

            time.sleep(5.0)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()


def publish_device_command(device_id: str, command: int):
    """供 API 调用，向指定下位机发送指令"""
    direction = DIRECTION_MAP.get(command, "未知")
    publisher = _get_mqtt_publisher()
    payload = {device_id: str(command)}
    topic = f"devices/{device_id}/command"
    publisher.publish(topic, payload, qos=1)
    return direction, topic


def start():
    """启动所有 MQTT 相关后台线程"""
    sub_thread = threading.Thread(target=_start_mqtt_subscriber, daemon=True)
    sub_thread.start()
    _start_mqtt_publisher()
