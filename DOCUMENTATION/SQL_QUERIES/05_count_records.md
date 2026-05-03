# SQL Query: Count Records (Statistics)

## Queries
```sql
SELECT COUNT(*) AS c FROM Student
SELECT COUNT(*) AS c FROM Instructor
SELECT COUNT(*) AS c FROM Subject
SELECT COUNT(*) AS c FROM Department
SELECT COUNT(*) AS c FROM Classroom
```

## Location
`/api/stats` endpoint - `api_stats()` function

## Purpose
Gathers system statistics by counting total records in each major table. Used for dashboard overview showing system scale.

## Parameters
None (global count across entire table)

## How It Works

```python
table_map = {
    "students": "Student",
    "instructors": "Instructor",
    "subjects": "Subject",
    "departments": "Department",
    "classrooms": "Classroom",
}
stats = {}
for key, table in table_map.items():
    row = db_query(f"SELECT COUNT(*) AS c FROM {table}", fetchone=True)
    stats[key] = row["c"]
```

1. **Loop through tables**: Iterates over each entity type
2. **Execute COUNT query**: Counts all rows in each table
3. **Store result**: Adds count to stats dictionary
4. **Return**: All counts returned together

## Example Response

```json
{
  "ok": true,
  "stats": {
    "students": 1250,
    "instructors": 42,
    "subjects": 87,
    "departments": 5,
    "classrooms": 30
  },
  "recent_students": [...]
}
```

## SQL Mechanics

### COUNT(*) Meaning
- Counts ALL rows in the table
- Includes NULL values
- Different from COUNT(column_name) which skips NULLs

### AS c Alias
- Renames result column to "c"
- Python code accesses as `row["c"]`

### Why fetchone=True
- COUNT(*) always returns exactly one row
- fetchone=True gets single dict instead of list
- Slightly more efficient for known single result

## Performance Analysis

### Index Strategy
COUNT(*) queries use different optimization paths:

#### Without Explicit Index
```sql
SELECT COUNT(*) FROM Student
```
- Can use any index on Student table
- Even on non-indexed table, MySQL counts rows efficiently
- Typical time: 10-50ms depending on table size

#### Optimized with Primary Key
```sql
SELECT COUNT(*) FROM Student  -- Student_ID is PK
```
- Uses primary key index (always exists)
- Very fast: O(1) with InnoDB index statistics
- Typical time: 1-5ms

### Performance by Table Size
```
Table Size    | Without Index | With Index | Improvement
10,000 rows   | 2-5ms        | 1-2ms      | 2-3x
100,000 rows  | 5-20ms       | 1-2ms      | 10-20x
1,000,000     | 50-100ms     | 1-2ms      | 50-100x
```

## Optimization Techniques

### Technique 1: Table Statistics (Best)
InnoDB maintains statistics on count:
```sql
SHOW TABLE STATUS LIKE 'Student'\G
-- Shows Rows field (approximate count)
```

### Technique 2: Count with Index
MySQL prefers smallest index:
```sql
-- If multiple indexes exist, uses smallest index
CREATE INDEX idx_student_id ON Student(Student_ID);
SELECT COUNT(*) FROM Student  -- Uses this index
```

### Technique 3: Approximate Count
If exact count not needed:
```sql
SELECT table_rows FROM information_schema.tables 
WHERE table_name = 'Student'
-- Very fast, may be slightly inaccurate
```

### Technique 4: Materialized View
For frequently accessed stats:
```sql
CREATE TABLE SystemStats AS
SELECT 
  (SELECT COUNT(*) FROM Student) as student_count,
  (SELECT COUNT(*) FROM Instructor) as instructor_count
  -- ... etc
```

## Query Pattern Analysis

### Problem with Current Implementation
```python
for key, table in table_map.items():
    row = db_query(f"SELECT COUNT(*) AS c FROM {table}", fetchone=True)
    stats[key] = row["c"]
```

**Issue**: 5 separate database queries (one per table)
- Connection overhead repeated 5 times
- Network roundtrips: 5
- Total time: ~50-100ms (with overhead)

### Better: Single Query
```sql
SELECT 
  (SELECT COUNT(*) FROM Student) as students,
  (SELECT COUNT(*) FROM Instructor) as instructors,
  (SELECT COUNT(*) FROM Subject) as subjects,
  (SELECT COUNT(*) FROM Department) as departments,
  (SELECT COUNT(*) FROM Classroom) as classrooms
```

**Improvement**: One query, one roundtrip
- Time: ~20-50ms (one overhead cost)
- More efficient

### Alternative: Stored Procedure
```sql
CREATE PROCEDURE GetStats(
  OUT p_students INT,
  OUT p_instructors INT,
  OUT p_subjects INT,
  OUT p_departments INT,
  OUT p_classrooms INT
)
BEGIN
  SELECT COUNT(*) INTO p_students FROM Student;
  SELECT COUNT(*) INTO p_instructors FROM Instructor;
  SELECT COUNT(*) INTO p_subjects FROM Subject;
  SELECT COUNT(*) INTO p_departments FROM Department;
  SELECT COUNT(*) INTO p_classrooms FROM Classroom;
END
```

Allows backend to call: `CALL GetStats(@s, @i, @su, @d, @c)`

## Use Cases for COUNT Queries

### Dashboard Display
```
Total Students: 1,250
Total Instructors: 42
Total Courses: 87
```

### Validation
```python
if stats['classrooms'] == 0:
    # Cannot create teacher without department
    return error("No departments exist")
```

### Capacity Planning
```python
avg_students_per_classroom = stats['students'] / stats['classrooms']
if avg_students_per_classroom > 40:
    print("Need more classrooms")
```

### Monitoring/Alerts
```python
if stats['students'] > threshold:
    send_alert("System approaching capacity")
```

## Related Dashboard Query

### Get Recent Students (Part of Same Response)
```sql
SELECT Student_ID, Fname, Lname, Level FROM Student 
ORDER BY Student_ID DESC LIMIT 5
```

This query is also in api_stats():
```python
recent = db_query(
    "SELECT Student_ID, Fname, Lname, Level FROM Student ORDER BY Student_ID DESC LIMIT 5"
)
```

**Why combined?**: Both dashboard stats; fetched together; one endpoint call.

## Index Recommendations

### Recommended Indexes (Primary Keys Usually Sufficient)
```sql
-- These are typically already primary keys
CREATE UNIQUE INDEX idx_student_pk ON Student(Student_ID);
CREATE UNIQUE INDEX idx_instructor_pk ON Instructor(Emp_ID);
CREATE UNIQUE INDEX idx_subject_pk ON Subject(Subject_ID);
CREATE UNIQUE INDEX idx_dept_pk ON Department(Dept_ID);
CREATE UNIQUE INDEX idx_classroom_pk ON Classroom(Classroom_ID);
```

**Why**: COUNT(*) can use any index efficiently; primary keys usually sufficient.

## Scaling Considerations

### Problem at Large Scale
When database has millions of records:
- COUNT(*) becomes slow (even with index)
- Dashboard loads slowly
- Every page view triggers these queries

### Solution: Caching
```python
import redis

def api_stats():
    cache_key = "stats:dashboard"
    cached = redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Calculate stats
    stats = {...}
    
    # Cache for 5 minutes
    redis.setex(cache_key, 300, json.dumps(stats))
    return stats
```

**Benefit**: Dashboard loads instantly; background job updates cache.

### Solution: Separate Statistics Table
```sql
CREATE TABLE DashboardStats (
  stat_date DATE,
  student_count INT,
  instructor_count INT,
  subject_count INT,
  department_count INT,
  classroom_count INT,
  PRIMARY KEY (stat_date)
);

-- Populate daily via scheduled job
INSERT INTO DashboardStats VALUES (DATE(NOW()), ..., ..., ...);

-- Retrieve stats
SELECT * FROM DashboardStats WHERE stat_date = CURDATE();
```

## Security Considerations

### No Security Issues
- COUNT queries are read-only
- No sensitive data returned (just numbers)
- Cannot be used to infer individual data
- Can be cached/distributed safely

### Privacy
- Numbers are generally public (school size, etc.)
- Specific student data requires authentication

## Testing COUNT Queries

### Manual Testing
```sql
SELECT COUNT(*) FROM Student;  -- Returns current count
INSERT INTO Student VALUES (...);
SELECT COUNT(*) FROM Student;  -- Returns increased by 1
DELETE FROM Student WHERE Student_ID = 12345;
SELECT COUNT(*) FROM Student;  -- Returns decreased by 1
```

### Verify Data Consistency
```sql
-- All students have names
SELECT COUNT(*) FROM Student WHERE Fname IS NULL OR Lname IS NULL;
-- Should return 0

-- All linked students have users
SELECT COUNT(*) FROM Student s 
LEFT JOIN Users u ON s.User_ID = u.User_ID
WHERE s.User_ID IS NOT NULL AND u.User_ID IS NULL;
-- Should return 0
```

## Complete Stats Endpoint Response

```python
@app.route("/api/stats")
def api_stats():
    table_map = {
        "students": "Student",
        "instructors": "Instructor",
        "subjects": "Subject",
        "departments": "Department",
        "classrooms": "Classroom",
    }
    stats = {}
    
    # Multiple COUNT queries
    for key, table in table_map.items():
        row = db_query(f"SELECT COUNT(*) AS c FROM {table}", fetchone=True)
        stats[key] = row["c"]
    
    # Get recent students
    recent = db_query(
        "SELECT Student_ID, Fname, Lname, Level FROM Student ORDER BY Student_ID DESC LIMIT 5"
    )
    
    return jsonify({"ok": True, "stats": stats, "recent_students": recent})
```

This demonstrates combining multiple queries for a single endpoint response.

## Summary

- **Purpose**: Aggregate statistics for dashboard overview
- **Pattern**: Multiple COUNT queries in loop (could be optimized)
- **Performance**: Adequate for most systems; cache for scale
- **Security**: Safe; read-only; no sensitive data
- **Maintenance**: Keep table indexes healthy for fast counts
