import mysql.connector
from mysql.connector import Error
import os

DB_CONFIG = {
    "host":     os.environ.get("DB_HOST",     "localhost"),
    "user":     os.environ.get("DB_USER",     "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME",     "school_db"),
    "port":     int(os.environ.get("DB_PORT", "3306")),
    "autocommit": True,
}

def get_db():
    """Return a new MySQL connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"[DB ERROR] {e}")
        return None

def query(sql, params=None, fetchone=False):
    """Execute a SELECT query and return results as dicts."""
    conn = get_db()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params or ())
        return cursor.fetchone() if fetchone else cursor.fetchall()
    except Error as e:
        print(f"[QUERY ERROR] {e}\nSQL: {sql}")
        return None
    finally:
        conn.close()

def execute(sql, params=None):
    """Execute INSERT / UPDATE / DELETE. Returns lastrowid."""
    conn = get_db()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params or ())
        conn.commit()
        return cursor.lastrowid
    except Error as e:
        print(f"[EXECUTE ERROR] {e}\nSQL: {sql}")
        return None
    finally:
        conn.close()
