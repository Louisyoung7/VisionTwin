import sqlite3

DB_PATH = "visiontwin.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY,
            plate TEXT NOT NULL UNIQUE
        )
    """)
    conn.commit()
    return conn
