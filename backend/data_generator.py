import random
import math
from database import init_db, get_connection

VEHICLE_COUNT = 3
BOUNDS = 12
MAX_SPEED = 0.3

conn = init_db()
cursor = conn.cursor()


def generate_plate(vehicle_id):
    return f"A{vehicle_id:05d}"


class Vehicle:
    def __init__(self, vehicle_id):
        self.id = vehicle_id
        self.plate = generate_plate(vehicle_id)
        self.x = random.uniform(-BOUNDS/2, BOUNDS/2)
        self.z = random.uniform(-BOUNDS/2, BOUNDS/2)
        self.angle = random.uniform(0, 2 * math.pi)
        self.speed = random.uniform(0.05, MAX_SPEED)
        self.turn_rate = random.uniform(-0.03, 0.03)

        cursor.execute("INSERT OR IGNORE INTO vehicles (id, plate) VALUES (?, ?)",
                       (self.id, self.plate))
        conn.commit()

    def update(self):
        self.angle += self.turn_rate * random.uniform(0.8, 1.2)

        self.x += math.cos(self.angle) * self.speed
        self.z += math.sin(self.angle) * self.speed

        if abs(self.x) > BOUNDS / 2:
            self.angle = math.pi - self.angle
            self.x = max(-BOUNDS / 2, min(BOUNDS / 2, self.x))

        if abs(self.z) > BOUNDS / 2:
            self.angle = -self.angle
            self.z = max(-BOUNDS / 2, min(BOUNDS / 2, self.z))

        if random.random() < 0.01:
            self.turn_rate = random.uniform(-0.03, 0.03)

        if random.random() < 0.02:
            self.speed = random.uniform(0.05, MAX_SPEED)


vehicles = [Vehicle(i) for i in range(VEHICLE_COUNT)]
