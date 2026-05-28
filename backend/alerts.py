"""
告警管理 - 生成、存储告警数据
"""
import time
import threading

alerts: list[dict] = []
alerts_lock = threading.Lock()
ALERT_COOLDOWN = 10
_last_alert_time: dict[int, float] = {}


def check_and_generate_alert(sensor_id: int, level: str, methane_pct: float, location: list):
    """检查并生成告警（由 mqtt_broker 调用）"""
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
