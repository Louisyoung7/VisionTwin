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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS docked_vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate TEXT NOT NULL UNIQUE
        )
    """)

    # 甲烷浓度历史记录
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS methane_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id INTEGER,
            methane_percentage REAL,
            location_x REAL,
            location_z REAL,
            timestamp TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # 积分变化历史
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS score_change_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate TEXT NOT NULL,
            old_score INTEGER,
            new_score INTEGER,
            reason TEXT,
            timestamp TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # 告警历史（扩展字段用于坑洼告警）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alert_history (
            id INTEGER PRIMARY KEY,
            sensor_id INTEGER,
            plate TEXT,
            source TEXT,
            level TEXT,
            methane_percentage REAL,
            location TEXT,
            message TEXT,
            time TEXT,
            confirmed INTEGER DEFAULT 0,
            detection_id INTEGER,
            frame_id INTEGER,
            confidence REAL,
            bbox TEXT,
            image_filename TEXT,
            timestamp TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # 坑洼检测历史
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pothole_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            detection_id INTEGER,
            frame_id INTEGER,
            confidence REAL,
            bbox_x REAL,
            bbox_y REAL,
            bbox_w REAL,
            bbox_h REAL,
            image_filename TEXT,
            detection_time TEXT,
            timestamp TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)

    conn.commit()
    return conn


def update_vehicle_score(plate: str, followed_route: bool) -> int | None:
    """
    根据视觉模块反馈更新车辆积分
    followed_route=True: 不操作，返回当前积分
    followed_route=False: 扣1分，返回更新后积分
    返回 None 表示车辆不存在
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT score FROM vehicles WHERE plate = ?", (plate,))
    row = cursor.fetchone()
    if row is None:
        conn.close()
        return None

    if not followed_route:
        cursor.execute("UPDATE vehicles SET score = score - 1 WHERE plate = ?", (plate,))

    cursor.execute("SELECT score FROM vehicles WHERE plate = ?", (plate,))
    new_score = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return new_score


def get_vehicle_score(plate: str) -> int | None:
    """获取车辆积分，不存在返回 None"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT score FROM vehicles WHERE plate = ?", (plate,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def ensure_vehicle(plate: str) -> int:
    """确保车辆存在，不存在则创建（积分=100），返回积分"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO vehicles (plate, score) VALUES (?, 100)", (plate,))
    cursor.execute("SELECT score FROM vehicles WHERE plate = ?", (plate,))
    score = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return score


def delete_vehicle(plate: str):
    """删除车辆记录"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vehicles WHERE plate = ?", (plate,))
    conn.commit()
    conn.close()


def save_docked_vehicle(plate: str):
    """保存或更新停靠车辆，已存在则更新"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO docked_vehicles (plate)
        VALUES (?)
        ON CONFLICT(plate) DO NOTHING
    """, (plate,))
    conn.commit()
    conn.close()


def remove_docked_vehicle(plate: str):
    """从停靠表中移除车辆（当车辆重新开始行驶时调用）"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM docked_vehicles WHERE plate = ?", (plate,))
    conn.commit()
    conn.close()


def get_docked_vehicles():
    """获取所有停靠车辆"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, plate FROM docked_vehicles")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "plate": r[1]} for r in rows]


def get_all_vehicles():
    """获取数据库中所有车辆"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT plate, score FROM vehicles")
    rows = cursor.fetchall()
    conn.close()
    return [{"plate": r[0], "score": r[1]} for r in rows]


# ===== 甲烷浓度历史 =====

def save_methane_history(sensor_id: int, methane_percentage: float, location: list):
    """保存甲烷浓度历史记录"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO methane_history (sensor_id, methane_percentage, location_x, location_z)
        VALUES (?, ?, ?, ?)
    """, (sensor_id, methane_percentage, location[0] if len(location) > 0 else 0, location[2] if len(location) > 2 else 0))
    conn.commit()
    conn.close()


def get_methane_history(sensor_id: int = None, hours: int = 24, limit: int = 1000):
    """获取甲烷浓度历史记录"""
    conn = get_connection()
    cursor = conn.cursor()
    if sensor_id is not None:
        cursor.execute("""
            SELECT sensor_id, methane_percentage, location_x, location_z, timestamp
            FROM methane_history
            WHERE sensor_id = ? AND timestamp >= datetime('now', '-' || ? || ' hours')
            ORDER BY timestamp DESC LIMIT ?
        """, (sensor_id, hours, limit))
    else:
        cursor.execute("""
            SELECT sensor_id, methane_percentage, location_x, location_z, timestamp
            FROM methane_history
            WHERE timestamp >= datetime('now', '-' || ? || ' hours')
            ORDER BY timestamp DESC LIMIT ?
        """, (hours, limit))
    rows = cursor.fetchall()
    conn.close()
    return [{"sensor_id": r[0], "methane_percentage": r[1], "location": [r[2], 0, r[3]], "timestamp": r[4]} for r in rows]


# ===== 积分变化历史 =====

def save_score_change(plate: str, old_score: int, new_score: int, reason: str):
    """保存积分变化记录"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO score_change_history (plate, old_score, new_score, reason)
        VALUES (?, ?, ?, ?)
    """, (plate, old_score, new_score, reason))
    conn.commit()
    conn.close()


def get_score_change_history(plate: str = None, hours: int = 24, limit: int = 1000):
    """获取积分变化历史"""
    conn = get_connection()
    cursor = conn.cursor()
    if plate is not None:
        cursor.execute("""
            SELECT plate, old_score, new_score, reason, timestamp
            FROM score_change_history
            WHERE plate = ? AND timestamp >= datetime('now', '-' || ? || ' hours')
            ORDER BY timestamp DESC LIMIT ?
        """, (plate, hours, limit))
    else:
        cursor.execute("""
            SELECT plate, old_score, new_score, reason, timestamp
            FROM score_change_history
            WHERE timestamp >= datetime('now', '-' || ? || ' hours')
            ORDER BY timestamp DESC LIMIT ?
        """, (hours, limit))
    rows = cursor.fetchall()
    conn.close()
    print(f"[DB] 查询积分历史: plate={plate}, hours={hours}, 结果数={len(rows)}")
    return [{"plate": r[0], "old_score": r[1], "new_score": r[2], "reason": r[3], "timestamp": r[4]} for r in rows]


# ===== 告警历史 =====

def save_alert_history(alert: dict):
    """保存告警到历史记录"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO alert_history
        (id, sensor_id, plate, source, level, methane_percentage, location, message, time,
         confirmed, detection_id, frame_id, confidence, bbox, image_filename)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        alert.get("id"),
        alert.get("sensor_id"),
        alert.get("plate"),
        alert.get("source"),
        alert.get("level"),
        alert.get("methane_percentage"),
        str(alert.get("location", [])),
        alert.get("message"),
        alert.get("time"),
        1 if alert.get("confirmed") else 0,
        alert.get("detection_id"),
        alert.get("frame_id"),
        alert.get("confidence"),
        str(alert.get("bbox", {})),
        alert.get("image_filename")
    ))
    conn.commit()
    conn.close()


def get_alert_history(source: str = None, level: str = None, hours: int = 24, limit: int = 500):
    """获取告警历史"""
    conn = get_connection()
    cursor = conn.cursor()
    query = """SELECT id, sensor_id, plate, source, level, methane_percentage, location,
               message, time, confirmed, detection_id, frame_id, confidence, bbox,
               image_filename, timestamp
               FROM alert_history
               WHERE timestamp >= datetime('now', '-' || ? || ' hours')"""
    params = [hours]

    if source:
        query += " AND source = ?"
        params.append(source)
    if level:
        query += " AND level = ?"
        params.append(level)

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [{
        "id": r[0], "sensor_id": r[1], "plate": r[2], "source": r[3], "level": r[4],
        "methane_percentage": r[5], "location": eval(r[6]) if r[6] else [],
        "message": r[7], "time": r[8], "confirmed": bool(r[9]),
        "detection_id": r[10], "frame_id": r[11], "confidence": r[12],
        "bbox": eval(r[13]) if r[13] else {},
        "image_filename": r[14], "timestamp": r[15]
    } for r in rows]


# ===== 统计数据 =====

def get_alert_stats(hours: int = 24):
    """获取告警统计数据"""
    conn = get_connection()
    cursor = conn.cursor()

    # 总告警数
    cursor.execute("SELECT COUNT(*) FROM alert_history WHERE timestamp >= datetime('now', '-' || ? || ' hours')", (hours,))
    total = cursor.fetchone()[0]

    # 按来源分组
    cursor.execute("""
        SELECT source, COUNT(*) FROM alert_history
        WHERE timestamp >= datetime('now', '-' || ? || ' hours')
        GROUP BY source
    """, (hours,))
    by_source = {r[0]: r[1] for r in cursor.fetchall()}

    # 按级别分组
    cursor.execute("""
        SELECT level, COUNT(*) FROM alert_history
        WHERE timestamp >= datetime('now', '-' || ? || ' hours')
        GROUP BY level
    """, (hours,))
    by_level = {r[0]: r[1] for r in cursor.fetchall()}

    # 传感器最高浓度
    cursor.execute("""
        SELECT sensor_id, MAX(methane_percentage) FROM methane_history
        WHERE timestamp >= datetime('now', '-' || ? || ' hours')
    """, (hours,))
    max_methane = cursor.fetchone()

    conn.close()
    return {
        "total_alerts": total,
        "by_source": by_source,
        "by_level": by_level,
        "max_methane_sensor": max_methane[0],
        "max_methane_value": max_methane[1]
    }


# ===== 坑洼检测历史 =====

def save_pothole_history(detections: list, frame_id: int, image_filename: str, detection_time: str):
    """保存一组坑洼检测记录"""
    conn = get_connection()
    cursor = conn.cursor()
    for d in detections:
        b = d.get("bbox", {})
        cursor.execute("""
            INSERT INTO pothole_history
            (detection_id, frame_id, confidence, bbox_x, bbox_y, bbox_w, bbox_h, image_filename, detection_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            d.get("id"),
            frame_id,
            d.get("confidence"),
            b.get("x"),
            b.get("y"),
            b.get("w"),
            b.get("h"),
            image_filename,
            detection_time
        ))
    conn.commit()
    conn.close()


def get_pothole_history(hours: int = 24, limit: int = 500):
    """获取坑洼检测历史"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, detection_id, frame_id, confidence, bbox_x, bbox_y, bbox_w, bbox_h,
               image_filename, detection_time, timestamp
        FROM pothole_history
        WHERE timestamp >= datetime('now', '-' || ? || ' hours')
        ORDER BY timestamp DESC LIMIT ?
    """, (hours, limit))
    rows = cursor.fetchall()
    conn.close()
    return [{
        "id": r[0],
        "detection_id": r[1],
        "frame_id": r[2],
        "confidence": r[3],
        "bbox": {"x": r[4], "y": r[5], "w": r[6], "h": r[7]},
        "image_filename": r[8],
        "detection_time": r[9],
        "timestamp": r[10]
    } for r in rows]