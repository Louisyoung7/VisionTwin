import sqlite3

DB_PATH = "visiontwin.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    """Initialize database with all tables."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY,
            plate TEXT NOT NULL UNIQUE,
            score INTEGER DEFAULT 100
        )
    """)

    cursor.execute("PRAGMA table_info(vehicles)")
    columns = [col[1] for col in cursor.fetchall()]
    if "score" not in columns:
        cursor.execute("ALTER TABLE vehicles ADD COLUMN score INTEGER DEFAULT 100")
        cursor.execute("UPDATE vehicles SET score = 100 WHERE score IS NULL")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS methane_sensors (
            id INTEGER PRIMARY KEY,
            location_x REAL,
            location_z REAL
        )
    """)

    conn.commit()
    return conn


def update_vehicle_score(vehicle_id: int, followed_route: bool) -> int | None:
    """
    根据视觉模块反馈更新车辆积分
    followed_route=True: 不操作，返回当前积分
    followed_route=False: 扣1分，返回更新后积分
    返回 None 表示车辆不存在
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT score FROM vehicles WHERE id = ?", (vehicle_id,))
    row = cursor.fetchone()
    if row is None:
        conn.close()
        return None

    if not followed_route:
        cursor.execute("UPDATE vehicles SET score = score - 1 WHERE id = ?", (vehicle_id,))

    cursor.execute("SELECT score FROM vehicles WHERE id = ?", (vehicle_id,))
    new_score = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return new_score


def get_vehicle_score(vehicle_id: int) -> int | None:
    """获取车辆积分，不存在返回 None"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT score FROM vehicles WHERE id = ?", (vehicle_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def ensure_vehicle(vehicle_id: int, plate: str = None) -> int:
    """确保车辆存在，不存在则创建（积分=100），返回积分"""
    if plate is None:
        plate = f"V{vehicle_id:04d}"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO vehicles (id, plate, score) VALUES (?, ?, 100)", (vehicle_id, plate))
    cursor.execute("SELECT score FROM vehicles WHERE id = ?", (vehicle_id,))
    score = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return score


def delete_vehicle(vehicle_id: int):
    """删除车辆记录"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))
    conn.commit()
    conn.close()


def close_connection(conn):
    """Close database connection."""
    if conn:
        conn.close()