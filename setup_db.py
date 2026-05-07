"""
Import the Galala International School database schema.

Usage:
    python setup_db.py

After import, create at least one admin account directly in MySQL
before logging into the app.
"""
import getpass
import os
import subprocess
import sys


MYSQL_PATH = os.environ.get("MYSQL_EXE", r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe")
SQL_FILE = os.path.join(os.path.dirname(__file__), "db.sql")


def main():
    print("=" * 55)
    print("  Galala SIS Database Setup")
    print("=" * 55)
    host = input("MySQL host     [localhost]: ").strip() or "localhost"
    user = input("MySQL username [root]:     ").strip() or "root"
    password = getpass.getpass("MySQL password (hidden):   ")

    result = subprocess.run(
        [MYSQL_PATH, f"-h{host}", f"-u{user}", f"-p{password}", "--execute", f"source {SQL_FILE}"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("\n[ERROR] MySQL import failed:")
        print(result.stderr)
        sys.exit(1)

    print("\nDatabase imported successfully.")
    print("Set DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, and DB_PORT in your environment before starting the app.")
    print("Start the app with: python app.py")
    print("Then start the app and log in with an existing admin account.")


if __name__ == "__main__":
    main()
