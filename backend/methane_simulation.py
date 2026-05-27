import random
import time
from db import init_db

BOUNDS = 12
MAX_METHANE = 100.0
MIN_METHANE = 0.0
METHANE_FLUCTUATION = 5.0
METHANE_WARNING_THRESHOLD = 40.0
METHANE_DANGER_THRESHOLD = 70.0


class Alert:
    def __init__(self, sensor_id: int, level: str, methane_percentage: float, location_x: float, location_z: float):
        self.id = int(time.time() * 1000) + sensor_id
        self.sensor_id = sensor_id
        self.level = level
        self.methane_percentage = round(methane_percentage, 2)
        self.location = [round(location_x, 2), 0.0, round(location_z, 2)]
        self.message = self._generate_message()
        self.time = time.strftime("%H:%M:%S")

    def _generate_message(self):
        if self.level == "danger":
            return f"甲烷浓度危险告警：传感器 #{self.sensor_id} 检测到 {self.methane_percentage}%"
        return f"甲烷浓度预警：传感器 #{self.sensor_id} 检测到 {self.methane_percentage}%"

    def to_dict(self):
        return {
            "id": self.id,
            "sensor_id": self.sensor_id,
            "level": self.level,
            "methane_percentage": self.methane_percentage,
            "location": self.location,
            "message": self.message,
            "time": self.time
        }


class Methane:
    def __init__(self, sensor_id: int, location_x: float, location_z: float):
        self.id = sensor_id
        self.location_x = location_x
        self.location_z = location_z
        self.methane_percentage = random.uniform(MIN_METHANE, MAX_METHANE / 4)
        self.last_update = time.time()
        self._last_percentage = self.methane_percentage

    def update(self):
        self._last_percentage = self.methane_percentage
        self.methane_percentage += random.uniform(-METHANE_FLUCTUATION, METHANE_FLUCTUATION)
        self.methane_percentage = max(MIN_METHANE, min(MAX_METHANE, self.methane_percentage))
        self.last_update = time.time()
        return self._check_threshold_crossed()

    def _check_threshold_crossed(self):
        crossed = []
        if self._last_percentage < METHANE_DANGER_THRESHOLD and self.methane_percentage >= METHANE_DANGER_THRESHOLD:
            crossed.append(("danger", self.methane_percentage))
        elif self._last_percentage < METHANE_WARNING_THRESHOLD and self.methane_percentage >= METHANE_WARNING_THRESHOLD:
            crossed.append(("warning", self.methane_percentage))
        elif self._last_percentage >= METHANE_WARNING_THRESHOLD and self.methane_percentage < METHANE_WARNING_THRESHOLD:
            crossed.append(("normal", self.methane_percentage))
        return crossed

    def get_data(self):
        return {
            "id": self.id,
            "location": [round(self.location_x, 2), 0.0, round(self.location_z, 2)],
            "methane_percentage": round(self.methane_percentage, 2),
            "last_update": self.last_update
        }


SENSOR_COUNT = 5
methane_sensors = []
alerts = []
ALERT_COOLDOWN = 10
_last_alert_time = {}


def init_methane_sensors():
    conn = init_db()
    cursor = conn.cursor()
    for i in range(SENSOR_COUNT):
        x = random.uniform(-BOUNDS / 2, BOUNDS / 2)
        z = random.uniform(-BOUNDS / 2, BOUNDS / 2)
        sensor = Methane(i, x, z)
        methane_sensors.append(sensor)
        _last_alert_time[i] = 0
        cursor.execute(
            "INSERT OR IGNORE INTO methane_sensors (id, location_x, location_z) VALUES (?, ?, ?)",
            (sensor.id, sensor.location_x, sensor.location_z)
        )
    conn.commit()
    conn.close()


def update_all_sensors():
    new_alerts = []
    for sensor in methane_sensors:
        crossings = sensor.update()
        current_time = time.time()
        for level, percentage in crossings:
            if level in ("warning", "danger"):
                if current_time - _last_alert_time.get(sensor.id, 0) >= ALERT_COOLDOWN:
                    alert = Alert(sensor.id, level, percentage, sensor.location_x, sensor.location_z)
                    alerts.insert(0, alert)
                    _last_alert_time[sensor.id] = current_time
                    new_alerts.append(alert)
    if len(alerts) > 50:
        alerts[:] = alerts[:50]
    return new_alerts


def get_alerts():
    return [a.to_dict() for a in alerts]


init_methane_sensors()
