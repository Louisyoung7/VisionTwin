import math
from db import init_db

VEHICLE_COUNT = 3
BOUNDS = 12
MAX_SPEED = 0.3


def generate_plate(vehicle_id):
    return f"A{vehicle_id:05d}"


class Vehicle:
    """车辆基类"""
    def __init__(self, vehicle_id):
        self.id = vehicle_id
        self.plate = generate_plate(vehicle_id)
        self.x = 0.0
        self.z = 0.0
        self.angle = 0.0
        self.speed = MAX_SPEED
        self.movement_type = "base"

    def update(self):
        """子类需要重写此方法"""
        pass


class SquareVehicle(Vehicle):
    """正方形轨迹车辆"""
    def __init__(self, vehicle_id):
        super().__init__(vehicle_id)
        self.movement_type = "square"
        self.square_size = BOUNDS / 4 - 0.5  # 缩小正方形边长
        self.corners = [
            (-self.square_size, -self.square_size),  # 左下
            (self.square_size, -self.square_size),   # 右下
            (self.square_size, self.square_size),     # 右上
            (-self.square_size, self.square_size)     # 左上
        ]
        self.current_corner = 0
        self.x = self.corners[0][0]
        self.z = self.corners[0][1]
        self.speed = 0.15  # 慢一点，方便观察

    def update(self):
        target_x, target_z = self.corners[self.current_corner]

        dx = target_x - self.x
        dz = target_z - self.z
        distance = math.sqrt(dx * dx + dz * dz)

        if distance < 0.1:
            self.current_corner = (self.current_corner + 1) % 4
            return

        self.angle = math.atan2(dz, dx)
        self.x += math.cos(self.angle) * self.speed
        self.z += math.sin(self.angle) * self.speed


class LineVehicle(Vehicle):
    """直线往返车辆"""
    def __init__(self, vehicle_id):
        super().__init__(vehicle_id)
        self.movement_type = "line"
        self.start_x = -BOUNDS / 4 + 1  # 缩小范围
        self.end_x = BOUNDS / 4 - 1
        self.z = 0.0
        self.x = self.start_x
        self.direction = 1  # 1 = 向右, -1 = 向左
        self.speed = 0.2

    def update(self):
        self.x += self.direction * self.speed

        if self.x >= self.end_x:
            self.x = self.end_x
            self.direction = -1
        elif self.x <= self.start_x:
            self.x = self.start_x
            self.direction = 1


class CircleVehicle(Vehicle):
    """圆形轨迹车辆"""
    def __init__(self, vehicle_id):
        super().__init__(vehicle_id)
        self.movement_type = "circle"
        self.center_x = 0.0
        self.center_z = 0.0
        self.radius = BOUNDS / 4 - 0.5  # 缩小圆形半径
        self.angle = 0.0
        self.x = self.center_x + self.radius
        self.z = self.center_z
        self.speed = 0.05  # 角速度，每帧转动多少弧度

    def update(self):
        self.angle += self.speed
        self.x = self.center_x + math.cos(self.angle) * self.radius
        self.z = self.center_z + math.sin(self.angle) * self.radius


def init_vehicles():
    conn = init_db()
    cursor = conn.cursor()

    # 创建三种不同类型的车辆
    vehicles = [
        SquareVehicle(0),      # 车辆0: 正方形轨迹
        LineVehicle(1),        # 车辆1: 直线往返
        CircleVehicle(2)       # 车辆2: 圆形轨迹
    ]

    for v in vehicles:
        cursor.execute("INSERT OR IGNORE INTO vehicles (id, plate) VALUES (?, ?)",
                       (v.id, v.plate))
    conn.commit()
    conn.close()
    return vehicles


vehicles = init_vehicles()
