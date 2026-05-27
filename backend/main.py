from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import time
import threading

from mqtt_client import MQTTClient

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 车辆数据（来自视觉模块 WebSocket）====================
vehicles: dict[int, dict] = {}
vehicles_lock = threading.Lock()

# ==================== 甲烷传感器数据（来自 MQTT）====================
mqtt_sensors: dict[int, dict] = {}
mqtt_sensors_lock = threading.Lock()

# ==================== 告警相关 ====================
alerts: list[dict] = []
alerts_lock = threading.Lock()
ALERT_COOLDOWN = 10
_last_alert_time: dict[int, float] = {}
WARNING_THRESHOLD = 40.0
DANGER_THRESHOLD = 70.0

# ==================== 前端 WebSocket 客户端 ====================
frontend_clients: set[WebSocket] = set()
frontend_clients_lock = threading.Lock()


def _generate_alert(sensor_id: int, level: str, methane_pct: float, location: list):
    """生成告警"""
    current_time = time.time()
    if current_time - _last_alert_time.get(sensor_id, 0) < ALERT_COOLDOWN:
        return None

    _last_alert_time[sensor_id] = current_time
    alert = {
        "id": int(current_time * 1000) + sensor_id,
        "sensor_id": sensor_id,
        "level": level,
        "methane_percentage": round(methane_pct, 2),
        "location": location,
        "message": f"甲烷浓度{'危险告警' if level == 'danger' else '预警'}：传感器 #{sensor_id} 检测到 {methane_pct:.1f}%",
        "time": time.strftime("%H:%M:%S")
    }
    with alerts_lock:
        alerts.insert(0, alert)
        if len(alerts) > 50:
            alerts[:] = alerts[:50]
    return alert


def _on_methane_message(topic: str, payload: bytes):
    """MQTT 消息回调 - 处理甲烷传感器数据"""
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
            _generate_alert(sensor_id, "danger", methane_pct, location)
        elif old_pct < WARNING_THRESHOLD <= methane_pct < DANGER_THRESHOLD:
            _generate_alert(sensor_id, "warning", methane_pct, location)

    except Exception as e:
        print(f"[MQTT] 解析甲烷数据失败: {e}")


# ==================== MQTT 订阅（后台线程）====================
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


_mqtt_thread = threading.Thread(target=_start_mqtt_subscriber, daemon=True)
_mqtt_thread.start()


# ==================== 视觉模块 WebSocket 接收 ====================

@app.websocket("/ws/vision")
async def ws_vision(websocket: WebSocket):
    """接收视觉模块推送的车辆数据"""
    await websocket.accept()
    print("[WebSocket] 视觉模块已连接")

    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                vehicle_list = payload.get("vehicles", [])

                with vehicles_lock:
                    for v in vehicle_list:
                        vid = v.get("id")
                        if vid is not None:
                            vehicles[vid] = v

                # 广播给所有前端客户端
                with frontend_clients_lock:
                    dead_clients = set()
                    for client in frontend_clients:
                        try:
                            await client.send_json({"vehicles": vehicle_list})
                        except Exception:
                            dead_clients.add(client)
                    for dead in dead_clients:
                        frontend_clients.discard(dead)

            except json.JSONDecodeError:
                print(f"[WebSocket] 解析视觉数据失败: {data[:100]}")

    except Exception as e:
        print(f"[WebSocket] 视觉模块连接异常: {e}")
    finally:
        print("[WebSocket] 视觉模块已断开")


# ==================== 前端 WebSocket 端点 ====================

@app.websocket("/ws")
async def ws_frontend(websocket: WebSocket):
    """前端 WebSocket 客户端连接"""
    await websocket.accept()
    print("[WebSocket] 前端客户端已连接")
    with frontend_clients_lock:
        frontend_clients.add(websocket)
    try:
        while True:
            # 保持连接，不主动关闭
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        with frontend_clients_lock:
            frontend_clients.discard(websocket)
        print("[WebSocket] 前端客户端已断开")


# ==================== REST API ====================

@app.get("/api/vehicles")
async def get_vehicles():
    """获取所有车辆数据（来自视觉模块）"""
    with vehicles_lock:
        vehicle_list = list(vehicles.values())
    return JSONResponse({"vehicles": vehicle_list})


@app.get("/api/vehicles/{vehicle_id}")
async def get_vehicle(vehicle_id: int):
    with vehicles_lock:
        vehicle = vehicles.get(vehicle_id)
    if vehicle is None:
        return JSONResponse({"error": "Vehicle not found"}, status_code=404)
    return JSONResponse(vehicle)


@app.get("/api/methane")
async def get_methane():
    """获取所有甲烷传感器数据（来自 MQTT）"""
    with mqtt_sensors_lock:
        sensor_list = list(mqtt_sensors.values())
    return JSONResponse({"methane": sensor_list})


@app.get("/api/methane/{sensor_id}")
async def get_methane_sensor(sensor_id: int):
    with mqtt_sensors_lock:
        sensor = mqtt_sensors.get(sensor_id)
    if sensor is None:
        return JSONResponse({"error": "Sensor not found"}, status_code=404)
    return JSONResponse(sensor)


@app.get("/api/alerts")
async def get_alerts():
    """获取告警列表"""
    with alerts_lock:
        return JSONResponse({"alerts": list(alerts)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
