import mysql.connector
from mysql.connector import Error
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


def _load_local_env_file():
    env_path = Path(__file__).resolve().parent / ".env"
    if load_dotenv:
        load_dotenv(env_path)
        return
    if not env_path.exists():
        return
    # Fallback parser when python-dotenv is unavailable.
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


_load_local_env_file()


def _required_env(name, allow_empty=False):
    raw_value = os.environ.get(name)
    if raw_value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    value = raw_value.strip()
    if not allow_empty and not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _required_int_env(name):
    value = _required_env(name)
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"Environment variable {name} must be an integer.") from exc


def _validate_db_user(username):
    allow_root = (os.environ.get("ALLOW_DB_ROOT") or "").strip().lower() == "true"
    if username.lower() == "root" and not allow_root:
        raise RuntimeError("Refusing to use DB_USER=root. Use a least-privileged DB user or set ALLOW_DB_ROOT=true explicitly.")
    return username


def _show_db_errors():
    return (os.environ.get("SHOW_DB_ERRORS") or "").strip().lower() == "true"


def _log_db_error(context, error):
    if _show_db_errors():
        print(f"[{context}] {error}")
    else:
        print(f"[{context}] Database operation failed.")


DB_CONFIG = {
    "host": _required_env("DB_HOST"),
    "user": _validate_db_user(_required_env("DB_USER")),
    "password": _required_env("DB_PASSWORD", allow_empty=True),
    "database": _required_env("DB_NAME"),
    "port": _required_int_env("DB_PORT"),
    "autocommit": True,
}

def get_db():
    """Return a new MySQL connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        _log_db_error("DB ERROR", e)
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
        _log_db_error("QUERY ERROR", e)
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
        _log_db_error("EXECUTE ERROR", e)
        return None
    finally:
        conn.close()
