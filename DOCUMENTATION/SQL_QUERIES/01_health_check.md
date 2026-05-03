# SQL Query: Health Check

## Query
```sql
SELECT 1 AS ok
```

## Location
`/api/health` endpoint - `api_health()` function

## Purpose
Tests database connectivity and server health.

## How It Works
- Selects the constant value `1` and aliases it as `ok`
- This query always succeeds if the database connection is working
- Takes minimal resources and time to execute

## Why This Pattern?
- Very simple query for minimal overhead
- If the database connection fails, this will immediately throw an error
- Perfect for health checks and monitoring

## Expected Result
```json
{
  "ok": true
}
```

## Response Codes
- **200 OK**: Database is reachable and working
- **500 Internal Server Error**: Database connection failed

## Usage
Frontend can call `/api/health` before making other requests to verify the backend is operational.

## Related Code
```python
@app.route("/api/health")
def api_health():
    db_query("SELECT 1 AS ok", fetchone=True)
    return jsonify({"ok": True})
```

---

# Performance Notes
- **Execution Time**: < 1ms typically
- **Index Usage**: None (constant query)
- **Scalability**: Always O(1) - constant time regardless of data size
- **Network Roundtrip**: Minimal for database connection test

# Variations
If you wanted more detailed health info, variations could include:
```sql
-- Check table accessibility
SELECT COUNT(*) FROM Student LIMIT 1;

-- Check replication status (if using MySQL replication)
SHOW SLAVE STATUS;

-- Check database size
SELECT table_schema, SUM(data_length) FROM information_schema.tables GROUP BY table_schema;
```
