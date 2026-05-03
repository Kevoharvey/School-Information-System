# SQL Query: Update Student

## Query
```sql
UPDATE Student SET 
  Fname=%s, Lname=%s, Level=%s,
  Student_Email=%s, City=%s, Street=%s, Building_Num=%s, Birth_Date=%s
WHERE Student_ID=%s
```

## Location
`/api/students/<int:student_id>` endpoint (PUT) - `api_students_edit()` function

## Purpose
Modifies an existing student's information. Used by administrators to update student records.

## Parameters
- `Fname`: First name (required)
- `Lname`: Last name (required)
- `Level`: Academic level (optional)
- `Student_Email`: Email address (optional)
- `City`: City of residence (optional)
- `Street`: Street address (optional)
- `Building_Num`: Building number (optional)
- `Birth_Date`: Date of birth (optional)
- `Student_ID`: Which student to update (from URL)

## How It Works

```python
@app.route("/api/students/<int:student_id>", methods=["PUT"])
def api_students_edit(student_id):
    d = request.get_json(silent=True) or {}
    db_query(
        """UPDATE Student SET Fname=%s, Lname=%s, Level=%s,
           Student_Email=%s, City=%s, Street=%s, Building_Num=%s, Birth_Date=%s
           WHERE Student_ID=%s""",
        (d["fname"], d["lname"], d.get("level") or None,
         d.get("email") or None, d.get("city") or None,
         d.get("street") or None, d.get("building_num") or None,
         d.get("birth_date") or None, student_id),
        commit=True
    )
    return jsonify({"ok": True, "message": "Student updated!"})
```

## UPDATE Syntax Breakdown

### SET Clause
```sql
SET Fname=%s, Lname=%s, Level=%s, ...
```
- Specifies which columns to update
- Multiple columns separated by commas
- New values provided in VALUES or parameter list

### WHERE Clause
```sql
WHERE Student_ID=%s
```
- **Critical**: Specifies which row(s) to update
- Without WHERE: ALL rows would be updated (disaster!)
- WITH WHERE: Only matching row updated

### Parameter Order
```python
(fname, lname, level, email, city, street, building_num, birth_date, student_id)
# Order must match: SET columns first, then WHERE column last
```

## Example Request and Response

### Request
```json
{
  "fname": "John",
  "lname": "Doe-Smith",  // Name changed
  "level": 2,             // Promoted
  "email": "newemail@school.com",  // Updated
  "city": "Boston",       // Moved
  "street": "789 Park Ave",
  "building_num": 12,
  "birth_date": "2007-05-15"
}
```

### URL
```
PUT /api/students/10001
```

### Response
```json
{
  "ok": true,
  "message": "Student updated!"
}
```

### Before Update
```sql
SELECT * FROM Student WHERE Student_ID = 10001
-- | 10001 | John | Doe | 1 | 2007-05-15 | old@school.com | NYC | 123 Main | 5 |
```

### After Update
```sql
SELECT * FROM Student WHERE Student_ID = 10001
-- | 10001 | John | Doe-Smith | 2 | 2007-05-15 | newemail@school.com | Boston | 789 Park Ave | 12 |
```

## Important: WHERE Clause

### Danger of Missing WHERE
```sql
-- CATASTROPHIC - Updates EVERY student!
UPDATE Student SET Fname=%s, Lname=%s, ...
-- All 10,000 students renamed to same value!
```

### Protection in Code
```python
@app.route("/api/students/<int:student_id>", methods=["PUT"])
def api_students_edit(student_id):  # student_id in URL
    ...
    db_query(..., WHERE Student_ID=%s""",
             (..., student_id),  # student_id always in parameters
             commit=True
    )
```

The student_id is extracted from URL, not user input. Safe.

## Affected Rows

### Check How Many Updated
```python
cursor.rowcount  # Returns number of rows affected
```

### In this implementation:
- Always 0 or 1 (since Student_ID is unique)
- 0: Student doesn't exist (no error raised)
- 1: Student updated successfully

### Could Add Validation
```python
with db_cursor() as (db, cursor):
    cursor.execute(...UPDATE..., params)
    if cursor.rowcount == 0:
        return jsonify({"ok": False, "error": "Student not found"}), 404
    db.commit()
```

## NULL Handling in UPDATE

### Setting to NULL
```python
d.get("email") or None  # If empty string or missing, becomes NULL
```

### In Database
```sql
-- Student had email
UPDATE Student SET Student_Email=NULL WHERE Student_ID=10001

-- Student_Email is now NULL (unknown/empty)
SELECT * FROM Student WHERE Student_ID=10001
-- Student_Email column: NULL (not empty string, actual NULL)
```

### Querying NULL Values
```sql
-- Find students without email
SELECT * FROM Student WHERE Student_Email IS NULL

-- Find students with email
SELECT * FROM Student WHERE Student_Email IS NOT NULL
```

## Partial Updates

### Current Implementation
```python
# Must provide ALL fields in SET clause
UPDATE Student SET Fname=%s, Lname=%s, Level=%s, ...
```

**Problem**: If frontend only sends fname, others become NULL!

### Better Implementation (Partial Update)
```python
@app.route("/api/students/<int:student_id>", methods=["PATCH"])
def api_students_partial_update(student_id):
    d = request.get_json(silent=True) or {}
    
    updates = []
    params = []
    
    if "fname" in d:
        updates.append("Fname=%s")
        params.append(d["fname"])
    
    if "lname" in d:
        updates.append("Lname=%s")
        params.append(d["lname"])
    
    if "email" in d:
        updates.append("Student_Email=%s")
        params.append(d.get("email") or None)
    
    # Add more fields as needed
    
    if not updates:
        return jsonify({"ok": False, "error": "No fields to update"}), 400
    
    params.append(student_id)
    
    query = f"UPDATE Student SET {', '.join(updates)} WHERE Student_ID=%s"
    db_query(query, tuple(params), commit=True)
    
    return jsonify({"ok": True, "message": "Student updated!"})
```

**Benefit**: Only provided fields are updated; others remain unchanged.

## Performance Considerations

### Index on WHERE Clause
```sql
CREATE UNIQUE INDEX idx_student_pk ON Student(Student_ID);
```

**Speed**: Lookup is O(log n), very fast
- Finds student instantly
- Updates one row
- Rebuilds all indexes on that row

### Number of Updated Columns
```sql
-- Fast: Updating 1-2 columns
UPDATE Student SET Fname=%s WHERE Student_ID=%s

-- Slower: Updating many columns
UPDATE Student SET Fname=%s, Lname=%s, Email=%s, ..., Birth_Date=%s WHERE Student_ID=%s
```

**Time**: 1-5ms for single row update.

## Audit Trail

### Log Updates
```python
import logging

def api_students_edit(student_id):
    d = request.get_json(silent=True) or {}
    
    # Log what changed
    logging.info(f"Updating student {student_id}: {d}")
    
    db_query(..., commit=True)
    
    logging.info(f"Successfully updated student {student_id}")
    
    return jsonify({"ok": True, "message": "Student updated!"})
```

### Track Who Changed It
```python
if not session.get("user"):
    return jsonify({"ok": False, "error": "Not authenticated"}), 401

admin_id = session["user"]["id"]
logging.info(f"Admin {admin_id} updated student {student_id}: {d}")
```

## Validation

### Current Implementation
Minimal validation; relies on database type checking.

### Recommended Validation
```python
def api_students_edit(student_id):
    d = request.get_json(silent=True) or {}
    
    # Validate required fields
    if not d.get("fname") or not d.get("lname"):
        return jsonify({"ok": False, "error": "First and last name required"}), 400
    
    # Validate level
    level = d.get("level")
    if level is not None and (level < 1 or level > 4):
        return jsonify({"ok": False, "error": "Level must be 1-4"}), 400
    
    # Validate email format
    email = d.get("email")
    if email and not re.match(r"[^@]+@[^@]", email):
        return jsonify({"ok": False, "error": "Invalid email"}), 400
    
    # Validate birth date
    if d.get("birth_date"):
        try:
            datetime.strptime(d["birth_date"], "%Y-%m-%d")
        except ValueError:
            return jsonify({"ok": False, "error": "Invalid date format"}), 400
    
    # Proceed with update
    db_query(..., commit=True)
    return jsonify({"ok": True, "message": "Student updated!"})
```

## Concurrency Issues

### Race Condition Example
```
Admin A: Reads student (Level: 1)
Admin B: Reads student (Level: 1)
Admin A: Updates to Level: 2, commits
Admin B: Updates to Level: 1, commits
Result: Level is 1 (Admin A's change lost!)
```

### Solution: Optimistic Locking
```sql
-- Include version number in table
CREATE TABLE Student (
  ...,
  version INT DEFAULT 1,
  ...
);

-- Update only if version hasn't changed
UPDATE Student SET Fname=%s, Level=%s, version=version+1
WHERE Student_ID=%s AND version=%s
```

### Implementation
```python
# Check if update succeeded (version matched)
if cursor.rowcount == 0:
    return jsonify({
        "ok": False, 
        "error": "Record was modified by another user"
    }), 409
```

## Batch Updates

### Update Multiple Students
```sql
UPDATE Student SET Level=2 WHERE Level=1 AND Student_ID < 20000
```

### In Code
```python
db_query(
    "UPDATE Student SET Level=%s WHERE Level=%s AND Student_ID < %s",
    (2, 1, 20000),
    commit=True
)
```

## Transaction Isolation

### Update During Read
```python
# Read student
student = db_query("SELECT * FROM Student WHERE Student_ID=%s", (10001,), fetchone=True)

# Another process updates same student...

# Your update with potentially stale data
db_query("UPDATE Student SET ...", (..., 10001), commit=True)
```

**Risk**: Your update uses outdated information.

### Solution: Read-Modify-Write in Transaction
```python
with db_cursor() as (db, cursor):
    # Read
    cursor.execute("SELECT * FROM Student WHERE Student_ID=%s", (10001,))
    student = cursor.fetchone()
    
    # Modify
    new_data = {**student, 'fname': 'NewName'}
    
    # Write (all in same transaction)
    cursor.execute("UPDATE Student SET ... WHERE Student_ID=%s", (..., 10001))
    
    db.commit()
```

## Related Queries

### Update All Students in Level
```sql
UPDATE Student SET Level=2 WHERE Level=1
```

### Update with Conditional
```sql
-- Promote underaged students to Level 1
UPDATE Student SET Level=1 
WHERE TIMESTAMPDIFF(YEAR, Birth_Date, CURDATE()) < 18

-- Update based on address
UPDATE Student SET City='NewYork' WHERE Street LIKE '% Ave %'
```

### Update with JOIN
```sql
-- Update based on related table (e.g., update all students in specific department)
UPDATE Student s
JOIN Department d ON s.Department_ID = d.Dept_ID
SET s.Level=2
WHERE d.Dept_Name='Engineering'
```

## Common Mistakes

### Missing WHERE Clause
```python
# WRONG - Updates every student!
db_query("UPDATE Student SET Fname=%s", (new_name,), commit=True)
```

### Type Mismatch
```python
# WRONG - Level is INT, not string
d["level"] = "two"  # Should be: 2
db_query("UPDATE Student SET Level=%s", (d["level"],), commit=True)
```

### Forgot to Commit
```python
# WRONG - Changes not persisted
db_query("UPDATE Student SET ...", commit=False)
# Changes lost when connection closes!
```

## Testing

### Manual Test
```sql
-- Before
SELECT Student_ID, Fname, Lname, Level FROM Student WHERE Student_ID=10001;

-- Update
UPDATE Student SET Fname='NewName', Level=2 WHERE Student_ID=10001;

-- Verify
SELECT Student_ID, Fname, Lname, Level FROM Student WHERE Student_ID=10001;
```

### Verify No Unintended Changes
```sql
-- Make sure only one row affected
SELECT COUNT(*) FROM Student WHERE Level=2;
-- Should be 1 more than before
```

## Summary

- **Purpose**: Modify existing student information
- **Required**: Fname, Lname (in code)
- **Optional**: All other fields
- **Safety**: WHERE clause prevents bulk updates
- **Performance**: Fast; O(1) via unique index
- **Caution**: All fields set to provided values; NULL if omitted
- **Better**: Implement partial update if needed
- **Concurrency**: Consider optimistic locking for production
