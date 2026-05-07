"""
setup_db.py  —  Run this ONCE to import the database.
Usage:
    python setup_db.py
You will be prompted for your MySQL root password.
"""
import getpass, sys, os

MYSQL_PATH = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
SQL_FILE   = os.path.join(os.path.dirname(__file__), "db.sql")

print("=" * 55)
print("  Galala SIS — Database Setup")
print("=" * 55)
host     = input("MySQL host     [localhost]: ").strip() or "localhost"
user     = input("MySQL username [root]:     ").strip() or "root"
password = getpass.getpass("MySQL password (hidden):   ")

# ── Import SQL file ───────────────────────────────────────
import subprocess
result = subprocess.run(
    [MYSQL_PATH, f"-h{host}", f"-u{user}", f"-p{password}", "--execute", f"source {SQL_FILE}"],
    capture_output=True, text=True
)
if result.returncode != 0:
    print("\n[ERROR] MySQL import failed:")
    print(result.stderr)
    sys.exit(1)

print("\n✅  Database imported successfully!")

# ── Update db_config.py ───────────────────────────────────
config_path = os.path.join(os.path.dirname(__file__), "db_config.py")
with open(config_path, "r") as f:
    content = f.read()

content = content.replace("'host': 'localhost'", f"'host': '{host}'")
content = content.replace("'user': 'root'",      f"'user': '{user}'")
content = content.replace("'password': ''",       f"'password': '{password}'")

with open(config_path, "w") as f:
    f.write(content)

print("✅  db_config.py updated with your credentials.")
print("\n📌  You can now start the app:")
print("    python app.py")
print("    Then open: http://localhost:5000")
print("\n🔑  Login credentials:")
print("    Admin:   admin@galala.edu    / admin123")
print("    Teacher: sarah.h@galala.edu  / teacher123")
print("    Student: a.rivers@student.galala.edu / student123")
