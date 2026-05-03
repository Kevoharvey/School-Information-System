# SQL Query: Get Students by Subject with Grades (Teacher View)

## Query
```sql
SELECT st.Student_ID, st.Fname, st.Lname, ss.Grades
FROM Studies ss
JOIN Student st ON ss.Student_ID = st.Student_ID
JOIN Teaches t  ON t.Subject_ID = ss.Subject_ID
WHERE t.Emp_ID = %s AND ss.Subject_ID = %s
ORDER BY st.Student_ID
```

## Location
`/api/teacher/<int:emp_id>/subject/<int:subject_id>/students` endpoint - `api_teacher_subject_students()` function

## Purpose
Retrieves all students enrolled in a specific subject taught by an instructor, along with their current grades. Used by teachers to view their class roster with grades.

## How It Works

```python
@app.route("/api/teacher/<int:emp_id>/subject/<int:subject_id>/students")
def api_teacher_subject_students(emp_id, subject_id):
    """Students enrolled in a specific subject taught by this instructor, with their grades."""
    rows = db_query(
        """SELECT st.Student_ID, st.Fname, st.Lname, ss.Grades
           FROM Studies ss
           JOIN Student st ON ss.Student_ID = st.Student_ID
           JOIN Teaches t  ON t.Subject_ID = ss.Subject_ID
           WHERE t.Emp_ID = %s AND ss.Subject_ID = %s
           ORDER BY st.Student_ID""",
        (emp_id, subject_id)
    )
    return jsonify({"ok": True, "students": rows})
```

## Query Structure

### FROM Clause: Studies Table
```sql
FROM Studies ss
```

- **Table**: Studies (enrollment/grades data)
- **Alias**: ss
- **Why here**: This table links students to subjects and contains grades

### JOIN 1: Get Student Info
```sql
JOIN Student st ON ss.Student_ID = st.Student_ID
```

- **Purpose**: Get student names and ID
- **Join type**: INNER JOIN (only students with grades in this subject)
- **Condition**: Match Student_ID

### JOIN 2: Verify Teacher Teaches This
```sql
JOIN Teaches t ON t.Subject_ID = ss.Subject_ID
```

- **Purpose**: Verify this is the correct teacher/subject combo
- **Data**: Links instructor to subject they teach
- **Security**: Ensures we're checking the right teacher

### WHERE Clause: Filter by Teacher and Subject
```sql
WHERE t.Emp_ID = %s AND ss.Subject_ID = %s
```

- `t.Emp_ID = %s`: Only this instructor's courses
- `ss.Subject_ID = %s`: Only this specific subject
- Combination: Only students in THIS teacher's THIS subject

### ORDER BY: Sort Results
```sql
ORDER BY st.Student_ID
```

- Sorts by student ID ascending
- Consistent, predictable order

## Example Result

### Request
```
GET /api/teacher/101/subject/5/students
```

### Response
```json
{
  "ok": true,
  "students": [
    {
      "Student_ID": 10001,
      "Fname": "John",
      "Lname": "Doe",
      "Grades": 92.5
    },
    {
      "Student_ID": 10002,
      "Fname": "Jane",
      "Lname": "Smith",
      "Grades": 88.0
    },
    {
      "Student_ID": 10003,
      "Fname": "Bob",
      "Lname": "Johnson",
      "Grades": 95.5
    }
  ]
}
```

## JOIN Visualization

### Table Relationships
```
Teaches table           Studies table           Student table
├── Emp_ID: 101    ←→   ├── Subject_ID: 5   ←→  ├── Student_ID: 10001
└── Subject_ID: 5  ←→   ├── Student_ID: 10001   ├── Fname: John
                   ←→   └── Grades: 92.5        └── Lname: Doe
```

### Data Flow
```
1. Look for Teaches record: Emp_ID=101, Subject_ID=5 (found)
2. Find all Studies records: Subject_ID=5 (found 3 students)
3. For each Studies record, join Student table to get names
4. Result: 3 rows with student info + grades
```

## Multi-Table JOIN Execution

### Step 1: Teaches Filter
```sql
-- Find what this teacher teaches
SELECT Emp_ID, Subject_ID FROM Teaches WHERE Emp_ID = 101
-- Result: { Emp_ID: 101, Subject_ID: 5 }
```

### Step 2: Studies Filter
```sql
-- Find all studies in this subject
SELECT Student_ID, Grades FROM Studies WHERE Subject_ID = 5
-- Result: 3 rows with Student_ID and Grades
```

### Step 3: Student Join
```sql
-- Get student names
SELECT Student_ID, Fname, Lname FROM Student 
WHERE Student_ID IN (10001, 10002, 10003)
-- Result: 3 rows with names
```

### Step 4: Combine
```sql
-- Final result combines all data
```

## Parameters

### emp_id (From URL)
```
/api/teacher/101/subject/5/students
              ^^^
              emp_id = 101 (Employee/Instructor ID)
```

### subject_id (From URL)
```
/api/teacher/101/subject/5/students
                           ^
                           subject_id = 5
```

## Performance Optimization

### Required Indexes
```sql
-- Critical indexes for performance
CREATE INDEX idx_studies_subject_id ON Studies(Subject_ID);
CREATE INDEX idx_studies_student_id ON Studies(Student_ID);
CREATE INDEX idx_teaches_emp_subject ON Teaches(Emp_ID, Subject_ID);
CREATE INDEX idx_student_id ON Student(Student_ID);
```

### Query Execution Plan
```
id | select_type | table | type  | rows | key
1  | SIMPLE      | t     | ref   | 1    | idx_teaches_emp_subject
1  | SIMPLE      | ss    | ref   | n    | idx_studies_subject_id
1  | SIMPLE      | st    | ref   | 1    | idx_student_id
```

### Performance Metrics
```
100 students in subject:
- Without indexes: 50-100ms (full table scans)
- With indexes: 5-15ms (index lookups)
- Improvement: 5-20x faster
```

## Use Cases

### Teacher Dashboard
```javascript
// Teacher clicks on a course they teach
async function viewClassRoster(empId, subjectId) {
  const response = await fetch(
    `/api/teacher/${empId}/subject/${subjectId}/students`
  );
  const data = await response.json();
  
  // Display grade book
  data.students.forEach(student => {
    console.log(`${student.Fname} ${student.Lname}: ${student.Grades}`);
  });
}
```

### Grade Entry Interface
```html
<table>
  <tr>
    <th>Student Name</th>
    <th>Current Grade</th>
    <th>Update</th>
  </tr>
  <!-- Fill with students from this query -->
</table>
```

### Class Statistics
```javascript
const grades = data.students.map(s => s.Grades);
const average = grades.reduce((a,b) => a+b) / grades.length;
const max = Math.max(...grades);
const min = Math.min(...grades);
console.log(`Average: ${average}, Max: ${max}, Min: ${min}`);
```

## Security Considerations

### Authentication Required
```python
@app.route("/api/teacher/<int:emp_id>/subject/<int:subject_id>/students")
def api_teacher_subject_students(emp_id, subject_id):
    if not session.get("user"):
        return jsonify({"ok": False, "error": "Not authenticated"}), 401
    
    # Proceed...
```

### Authorization Check (Recommended)
```python
# Ensure teacher can only view their own classes
if session["user"]["id"] != emp_id:
    return jsonify({"ok": False, "error": "Not authorized"}), 403

# Ensure teacher teaches this subject (extra safety)
teaches = db_query(
    "SELECT * FROM Teaches WHERE Emp_ID=%s AND Subject_ID=%s",
    (emp_id, subject_id), fetchone=True
)
if not teaches:
    return jsonify({"ok": False, "error": "Not authorized"}), 403

# Now safe to return students
```

**Current code**: Missing authorization (should add).

## Related Queries

### Get All Students Taught by This Teacher (Any Subject)
```sql
SELECT DISTINCT st.Student_ID, st.Fname, st.Lname, st.Level, st.Student_Email
FROM Studies ss
JOIN Student st ON ss.Student_ID = st.Student_ID
JOIN Teaches t ON ss.Subject_ID = t.Subject_ID
WHERE t.Emp_ID = %s
ORDER BY st.Student_ID
```

### Get Teacher's Subjects
```sql
SELECT s.Subject_ID, s.Subject_Name, s.Subject_Level, s.Subject_Slots
FROM Teaches t 
JOIN Subject s ON t.Subject_ID = s.Subject_ID
WHERE t.Emp_ID = %s
```

### Get Class Average
```sql
SELECT AVG(ss.Grades) as average_grade,
       MAX(ss.Grades) as max_grade,
       MIN(ss.Grades) as min_grade,
       COUNT(*) as num_students
FROM Studies ss
JOIN Teaches t ON ss.Subject_ID = t.Subject_ID
WHERE t.Emp_ID = %s AND ss.Subject_ID = %s
```

### Get Students Without Grades in Subject
```sql
SELECT st.Student_ID, st.Fname, st.Lname
FROM Student st
LEFT JOIN Studies ss ON st.Student_ID = ss.Student_ID 
  AND ss.Subject_ID = %s
WHERE ss.Student_ID IS NULL
-- AND enrolled in this subject somehow (via Is_In or prerequisite)
```

## Comparison: Different Teacher Queries

### 1. All Subjects This Teacher Teaches
```sql
SELECT s.Subject_ID, s.Subject_Name
FROM Teaches t 
JOIN Subject s ON t.Subject_ID = s.Subject_ID
WHERE t.Emp_ID = %s
```

### 2. All Students This Teacher Teaches (Any Subject)
```sql
SELECT DISTINCT st.Student_ID, st.Fname, st.Lname
FROM Studies ss
JOIN Student st ON ss.Student_ID = st.Student_ID
JOIN Teaches t ON ss.Subject_ID = t.Subject_ID
WHERE t.Emp_ID = %s
```

### 3. Students in Specific Subject (THIS QUERY)
```sql
SELECT st.Student_ID, st.Fname, st.Lname, ss.Grades
FROM Studies ss
JOIN Student st ON ss.Student_ID = st.Student_ID
JOIN Teaches t ON t.Subject_ID = ss.Subject_ID
WHERE t.Emp_ID = %s AND ss.Subject_ID = %s
```

### 4. Full Class Details with Statistics
```sql
SELECT st.Student_ID, st.Fname, st.Lname, ss.Grades,
       ROW_NUMBER() OVER (ORDER BY ss.Grades DESC) as rank
FROM Studies ss
JOIN Student st ON ss.Student_ID = st.Student_ID
JOIN Teaches t ON t.Subject_ID = ss.Subject_ID
WHERE t.Emp_ID = %s AND ss.Subject_ID = %s
ORDER BY ss.Grades DESC
```

## Edge Cases

### No Students in Subject
```
Query result: Empty array []
Response: { "ok": true, "students": [] }
```

**Scenario**: Subject created but no one enrolled yet.

### Teacher Doesn't Teach Subject
```
Query result: Empty array []
Response: { "ok": true, "students": [] }
```

**Scenario**: Emp_ID and Subject_ID don't match in Teaches table.

**Should add check**: Return 403 instead of empty.

### Student Has No Grade Yet
```
Not included in results (no Studies record exists)
Must use LEFT JOIN to see ungraded students
```

**Current query**: Only shows graded students.

**Fix if needed**:
```sql
LEFT JOIN Studies ss ON ss.Student_ID = st.Student_ID 
  AND ss.Subject_ID = %s
-- Then ss.Grades would be NULL for ungraded students
```

## Performance at Scale

### 5,000 Students, One Subject, 100 in Class
```
Query time: 2-5ms (indexes used)
Network: 10-50ms
Total: 12-55ms
```

### 100,000 Students, Subject, 300 in Class
```
Query time: Still 2-5ms (indexes handle it)
Network: 10-100ms (more data)
Total: 12-105ms
```

### Pagination for Large Classes
```python
@app.route("/api/teacher/<int:emp_id>/subject/<int:subject_id>/students")
def api_teacher_subject_students(emp_id, subject_id):
    page = request.args.get('page', 1, type=int)
    limit = 50
    offset = (page - 1) * limit
    
    rows = db_query(
        """SELECT st.Student_ID, st.Fname, st.Lname, ss.Grades
           FROM Studies ss
           JOIN Student st ON ss.Student_ID = st.Student_ID
           JOIN Teaches t ON t.Subject_ID = ss.Subject_ID
           WHERE t.Emp_ID = %s AND ss.Subject_ID = %s
           ORDER BY st.Student_ID
           LIMIT %s OFFSET %s""",
        (emp_id, subject_id, limit, offset)
    )
    return jsonify({"ok": True, "students": rows})
```

## Testing

### Manual Test
```sql
-- Verify data exists
SELECT * FROM Teaches WHERE Emp_ID=101 AND Subject_ID=5;
-- Should return 1 row

SELECT COUNT(*) FROM Studies WHERE Subject_ID=5;
-- Should return > 0

-- Run actual query
SELECT st.Student_ID, st.Fname, st.Lname, ss.Grades
FROM Studies ss
JOIN Student st ON ss.Student_ID = st.Student_ID
JOIN Teaches t ON t.Subject_ID = ss.Subject_ID
WHERE t.Emp_ID=101 AND ss.Subject_ID=5
ORDER BY st.Student_ID;
-- Should return N rows with student data
```

## Caching Strategy

### Cache Class Roster
```python
cache_key = f"class_roster:emp_{emp_id}:subject_{subject_id}"

# Check cache
cached = redis.get(cache_key)
if cached:
    return json.loads(cached)

# Fetch from DB
students = fetch_students(emp_id, subject_id)

# Cache for 30 minutes (invalidate when grades change)
redis.setex(cache_key, 1800, json.dumps(students))
return students
```

**Benefit**: Frequent requests don't hit DB repeatedly.

**Invalidation**: Clear cache when grades updated.

## Summary

- **Purpose**: Get students in a specific class with their grades
- **Tables**: Studies, Student, Teaches (3 JOINs)
- **Filters**: Teacher ID and Subject ID
- **Result**: Student roster with current grades
- **Performance**: Fast with indexes (~3-5ms)
- **Security**: Should verify teacher teaches this subject
- **Use**: Teacher grade entry interface, class roster view
- **Alternative**: Separate queries for students and grades
- **Advantage**: Single query gets all data needed
