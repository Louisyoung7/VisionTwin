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
            plate TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS methane_sensors (
            id INTEGER PRIMARY KEY,
            location_x REAL,
            location_z REAL
        )
    """)

    conn.commit()
    return conn


def close_connection(conn):
    """Close database connection."""
    if conn:
        conn.close()