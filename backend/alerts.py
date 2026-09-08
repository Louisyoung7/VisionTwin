"""
告警管理 - 生成、存储告警数据
"""
import time
import threading
import os
from datetime import datetime

alerts: list[dict] = []
alerts_lock = threading.Lock()
ALERT_COOLDOWN = 10
_last_alert_time: dict[int, float] = {}

# 坑洼告警存储目录
ALERT_SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alerts")
IMAGE_SAVE_DIR = os.path.join(ALERT_SAVE_DIR, "pothole_images")
os.makedirs(IMAGE_SAVE_DIR, exist_ok=True)


def check_and_generate_alert(sensor_id: int, level: str, methane_pct: float, location: list):
    """检查并生成告警（由 mqtt_broker 调用，来源=传感器）"""
    from db import save_alert_history
    current_time = time.time()
    if current_time - _last_alert_time.get(sensor_id, 0) < ALERT_COOLDOWN:
        return None

    _last_alert_time[sensor_id] = current_time
    alert = {
        "id": int(current_time * 1000) + hash(sensor_id) % 1000,
        "sensor_id": sensor_id,
        "source": "sensor",
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
    # 保存到历史记录
    save_alert_history(alert)
    # 广播给前端
    from ws_endpoints import broadcast_alert_sync
    broadcast_alert_sync(alert)
    return alert


def generate_vehicle_alert(plate: str, level: str, followed: bool, location: list, route_id: int = None):
    """生成车辆告警（由 ws_endpoints 调用，来源=车辆）"""
    from db import save_alert_history
    current_time = time.time()
    key = f"vehicle_{plate}"
    if current_time - _last_alert_time.get(key, 0) < ALERT_COOLDOWN:
        return None

    _last_alert_time[key] = current_time
    alert = {
        "id": int(current_time * 1000) + hash(plate) % 10000,
        "plate": plate,
        "source": "vehicle",
        "level": level,
        "followed": followed,
        "location": location,
        "route_id": route_id,
        "message": f"车辆告警：{plate} 偏离规定路线" if not followed else f"车辆告警：{plate} 状态异常",
        "time": time.strftime("%H:%M:%S")
    }
    with alerts_lock:
        alerts.insert(0, alert)
        if len(alerts) > 50:
            alerts[:] = alerts[:50]
    # 保存到历史记录
    save_alert_history(alert)
    return alert


def generate_pothole_alert(data: dict, image_filename: str = None):
    """生成坑洼告警（由 api_routes 调用，来源=pothole）
    data: {"detections": [...], "total_count": N, "frame_id": N, "timestamp": float}
    """
    from db import save_alert_history, save_pothole_history
    current_time = time.time()
    detections = data.get("detections", [])
    total = data.get("total_count", len(detections))
    frame_id = data.get("frame_id", 0)
    ts = data.get("timestamp", time.time())
    det_time = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

    # 写日志
    log_file = os.path.join(ALERT_SAVE_DIR, "hole_log.txt")
    line = f"{det_time} | frame=#{frame_id} | count={total} | " + __import__("json").dumps(detections, ensure_ascii=False)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")

    # 保存到数据库（坑洼历史）
    save_pothole_history(detections, frame_id, image_filename or "", det_time)

    # 为每个坑洼生成告警
    last_alert = None
    for d in detections:
        key = f"pothole_{d.get('id')}_{frame_id}"
        if current_time - _last_alert_time.get(key, 0) < ALERT_COOLDOWN:
            continue
        _last_alert_time[key] = current_time

        b = d.get("bbox", {})
        alert = {
            "id": int(current_time * 1000) + d.get("id", 0),
            "source": "pothole",
            "level": "warning",
            "detection_id": d.get("id"),
            "frame_id": frame_id,
            "bbox": b,
            "confidence": d.get("confidence"),
            "location": [b.get("x", 0), 0, b.get("y", 0)],
            "det_time": det_time,
            "image_filename": image_filename,
            "message": f"坑洼告警：#{d.get('id')} 置信度={d.get('confidence', 0):.2f} 位置=({b.get('x')},{b.get('y')})",
            "time": time.strftime("%H:%M:%S")
        }
        with alerts_lock:
            alerts.insert(0, alert)
            if len(alerts) > 50:
                alerts[:] = alerts[:50]
        save_alert_history(alert)
        last_alert = alert

    return last_alert
