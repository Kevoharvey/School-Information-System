from db_config import execute, query

print("Testing Activity_Logs...")

# Try a manual insert
try:
    res = execute("INSERT INTO Activity_Logs (Action, Table_Name) VALUES (%s, %s)", ("Test Action", "Debug"))
    print(f"Insert successful, row ID: {res}")
except Exception as e:
    print(f"Insert failed: {e}")

# Try to query
try:
    rows = query("SELECT * FROM Activity_Logs")
    print(f"Query successful, found {len(rows) if rows else 0} rows.")
    if rows:
        for row in rows:
            print(f" - {row}")
except Exception as e:
    print(f"Query failed: {e}")
