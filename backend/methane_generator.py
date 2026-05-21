import random
import time
from database import init_db, get_connection

conn = init_db()
cursor = conn.cursor()

BOUNDS = 12
MAX_METHANE = 100.0
MIN_METHANE = 0.0
METHANE_FLUCTUATION = 5.0


class MethaneSensor:
    def __init__(self, sensor_id: int, location_x: float, location_z: float):
        self.id = sensor_id
        self.location_x = location_x
        self.location_z = location_z
        self.methane_percentage = random.uniform(MIN_METHANE, MAX_METHANE)
        self.last_update = time.time()

    def update(self):
        self.methane_percentage += random.uniform(-METHANE_FLUCTUATION, METHANE_FLUCTUATION)
        self.methane_percentage = max(MIN_METHANE, min(MAX_METHANE, self.methane_percentage))
        self.last_update = time.time()

    def get_data(self):
        return {
            "id": self.id,
            "location": [round(self.location_x, 2), 0.0, round(self.location_z, 2)],
            "methane_percentage": round(self.methane_percentage, 2),
            "last_update": self.last_update
        }


cursor.execute("""
    CREATE TABLE IF NOT EXISTS methane_sensors (
        id INTEGER PRIMARY KEY,
        location_x REAL,
        location_z REAL
    )
""")

SENSOR_COUNT = 5
methane_sensors = []


def init_methane_sensors():
    for i in range(SENSOR_COUNT):
        x = random.uniform(-BOUNDS / 2, BOUNDS / 2)
        z = random.uniform(-BOUNDS / 2, BOUNDS / 2)
        sensor = MethaneSensor(i, x, z)
        methane_sensors.append(sensor)
        cursor.execute(
            "INSERT OR IGNORE INTO methane_sensors (id, location_x, location_z) VALUES (?, ?, ?)",
            (sensor.id, sensor.location_x, sensor.location_z)
        )
    conn.commit()


init_methane_sensors()
