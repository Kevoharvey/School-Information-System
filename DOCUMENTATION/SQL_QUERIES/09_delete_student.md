# SQL Query: Delete Student with Cascade

## Queries
```sql
-- Step 1: Get the linked user
SELECT User_ID FROM Student WHERE Student_ID = %s

-- Step 2: Delete student (cascades to Studies)
DELETE FROM Student WHERE Student_ID = %s

-- Step 3: Delete linked user account (if exists)
DELETE FROM Users WHERE User_ID = %s
```

## Location
`/api/students/<int:student_id>` endpoint (DELETE) - `api_students_delete()` function

## Purpose
Completely removes a student from the system, including their login account and related records. Cleanup operation for admin management.

## How It Works

```python
@app.route("/api/students/<int:student_id>", methods=["DELETE"])
def api_students_delete(student_id):
    # Step 1: Look up the linked Users record before deleting
    student = db_query(
        "SELECT User_ID FROM Student WHERE Student_ID = %s",
        (student_id,), fetchone=True
    )
    
    # Step 2: Delete student (cascades to Studies)
    db_query("DELETE FROM Student WHERE Student_ID = %s", 
             (student_id,), commit=True)
    
    # Step 3: Also delete the Users login account if it exists
    if student and student.get("User_ID"):
        db_query("DELETE FROM Users WHERE User_ID = %s", 
                 (student["User_ID"],), commit=True)
    
    return jsonify({"ok": True, "message": "Student and login account deleted."})
```

## Step-by-Step Process

### Step 1: Fetch User_ID
```sql
SELECT User_ID FROM Student WHERE Student_ID = %s
```

**Why?**: Need User_ID to delete the login account afterward.

**Result**: 
```json
{
  "User_ID": 523
}
```

or `None` if no user linked.

### Step 2: Delete Student Record
```sql
DELETE FROM Student WHERE Student_ID = %s
```

**What happens**:
1. Removes row from Student table
2. **Cascading delete** (via foreign key): All Studies records with this Student_ID deleted
3. **No cascading delete** to Users (we handle separately)

**Example**: Student 10001 has 5 grade records
- Before: Student table has 1 row, Studies table has 5 rows
- After: Student table has 0 rows, Studies table has 0 rows

### Step 3: Delete User Account (Conditional)
```sql
DELETE FROM Users WHERE User_ID = %s
```

**Conditions**:
- Only executed if `student` is not None (student exists)
- Only executed if `User_ID` is not None (student had login)

**Result**: Removes authentication account.

## Foreign Key Relationships

### Database Schema
```
Users (Authentication)
├── User_ID (PK)
├── Email
├── Password
└── Role

Student (Student Data)
├── Student_ID (PK)
├── Fname, Lname
├── User_ID (FK → Users)
└── ...

Studies (Grades)
├── Student_ID (FK → Student) ← AUTO DELETE when Student deleted
├── Subject_ID (FK → Subject)
└── Grades
```

### Cascade Behavior
```sql
CREATE TABLE Studies (
  Student_ID INT,
  Subject_ID INT,
  Grades DECIMAL,
  PRIMARY KEY (Student_ID, Subject_ID),
  FOREIGN KEY (Student_ID) REFERENCES Student(Student_ID) 
    ON DELETE CASCADE  ← When Student deleted, delete Studies rows
);
```

**Effect**: When Student row deleted, all related Studies records auto-deleted.

## Why Two Separate Delete Calls?

### User_ID Relationship
```
Student table has: User_ID (foreign key)
Users table has: User_ID (primary key)

Database does NOT have CASCADE from Student to Users
```

**Why?**: Design decision
- Multiple students could theoretically share one user account (unlikely but possible)
- Better to explicitly handle: Delete student first, then user

### Explicit Handling
```python
# Manual check and delete
if student and student.get("User_ID"):
    db_query("DELETE FROM Users WHERE User_ID = %s", (student["User_ID"],), commit=True)
```

### Alternative Design (Auto-Cascade)
```sql
ALTER TABLE Student 
ADD CONSTRAINT fk_student_user 
FOREIGN KEY (User_ID) REFERENCES Users(User_ID)
ON DELETE CASCADE;

-- Then single delete:
DELETE FROM Student WHERE Student_ID = %s  -- Also deletes Users if cascade set
```

## Request and Response

### Request
```
DELETE /api/students/10001
```

### Response
```json
{
  "ok": true,
  "message": "Student and login account deleted."
}
```

## Error Scenarios

### Student Doesn't Exist
```sql
DELETE FROM Student WHERE Student_ID = 9999
-- Affects 0 rows, but no error raised
```

**Current code behavior**: Returns success (idempotent).

**Better behavior**: Check rowcount
```python
cursor.execute("DELETE FROM Student WHERE Student_ID = %s", (student_id,))
if cursor.rowcount == 0:
    return jsonify({"ok": False, "error": "Student not found"}), 404
```

### User_ID Not Found (Orphaned Record)
```python
if student and student.get("User_ID"):
    # This skips deletion if User_ID is None
    # Student deleted even if no user account
```

**Handling**: Student deleted even if no login account (correct).

## Data Consistency

### Scenarios

#### Scenario 1: Student with Login (Most Common)
```
Before:
  Users: { User_ID: 523, Email: john@school.com }
  Student: { Student_ID: 10001, User_ID: 523 }
  Studies: { Student_ID: 10001, Subject_ID: 5, Grades: 92 }

Delete:
  DELETE FROM Student WHERE Student_ID = 10001
  -- Studies deleted via cascade
  DELETE FROM Users WHERE User_ID = 523
  -- User account deleted

After:
  Users: (empty)
  Student: (empty)
  Studies: (empty)
```

#### Scenario 2: Student Without Login
```
Before:
  Users: (empty)
  Student: { Student_ID: 10001, User_ID: NULL }
  Studies: { Student_ID: 10001, Subject_ID: 5 }

Delete:
  DELETE FROM Student WHERE Student_ID = 10001
  -- Studies deleted via cascade
  if student.get("User_ID"):  -- NULL, so skipped
    -- No User deletion

After:
  Users: (empty)
  Student: (empty)
  Studies: (empty)
```

#### Scenario 3: User Account Orphaned
```
Before (Data Integrity Issue):
  Users: { User_ID: 523, Email: john@school.com }
  Student: (deleted by admin)
  
Current code:
  -- Can't happen: Step 1 looks up User_ID before deleting
  -- But if someone manually deleted Student without going through API:
  Users: { User_ID: 523 } still exists (orphaned)
```

## Performance

### Query Execution Time
```
SELECT User_ID: 1-2ms (indexed lookup)
DELETE FROM Student: 1-5ms (one row delete + cascade)
DELETE FROM Users: 1-2ms (indexed lookup + delete)
Total: 3-9ms
```

### Cascading Delete Performance
```sql
-- If student has many Studies records
DELETE FROM Student WHERE Student_ID = %s
-- All 50 Studies records deleted automatically
-- Time: 5-20ms for 50 cascaded records
```

### Indexes Help
```sql
CREATE INDEX idx_studies_student_id ON Studies(Student_ID);
-- Cascade uses this index to find records to delete
```

## Risks and Mitigations

### Risk 1: Accidental Deletion
```python
# WRONG - Deletes every student!
db_query("DELETE FROM Student", commit=True)

# PROTECTED - Always has WHERE clause
db_query("DELETE FROM Student WHERE Student_ID = %s", (student_id,), commit=True)
```

**Mitigation**: Always use WHERE clause with specific condition.

### Risk 2: Login Account Leak
```python
# Incorrect: User account left behind
db_query("DELETE FROM Student WHERE Student_ID = %s", commit=True)
# User account still exists, can still login!

# Protected: Explicitly delete user too
if student and student.get("User_ID"):
    db_query("DELETE FROM Users WHERE User_ID = %s", (student["User_ID"],), commit=True)
```

**Mitigation**: Explicit User deletion handles this.

### Risk 3: Related Data Issues
```sql
-- If someone is assigned to classroom via Is_In table:
Is_In: { Student_ID: 10001, Classroom_ID: 5 }

-- Current cascade only covers Studies, not Is_In
-- Is_In record remains (orphaned)
```

**Fix**: Either
1. Add CASCADE to Is_In foreign key
2. Manually delete Is_In before Student
3. Check for related records and reject deletion

### Risk 4: No Backup
```python
# After deletion, data is gone
db_query("DELETE FROM Student WHERE Student_ID = %s", commit=True)
# If mistake, must restore from backup (if exists)
```

**Mitigation**:
- Take backups regularly
- Implement soft deletes (mark as deleted, don't actually remove)
- Require admin confirmation for deletes

## Better Implementation (Soft Delete)

### Add "Deleted" Column
```sql
ALTER TABLE Student ADD COLUMN is_deleted BOOL DEFAULT FALSE;
```

### Soft Delete (Mark as Deleted)
```python
db_query(
    "UPDATE Student SET is_deleted=TRUE WHERE Student_ID = %s",
    (student_id,),
    commit=True
)

# Don't actually delete; just mark as deleted
# Can restore later if needed
```

### Query Students (Exclude Deleted)
```python
db_query(
    "SELECT * FROM Student WHERE is_deleted=FALSE ORDER BY Student_ID"
)
```

### Benefits
- **Recoverable**: Data not gone, just marked
- **Audit trail**: Can see who was deleted when
- **Relationships**: No cascade issues
- **Undo**: Easy to restore

### Drawbacks
- Need to add `is_deleted=FALSE` to all queries
- Database size grows
- More complex logic

## Audit Trail

### Log Deletion
```python
import logging

def api_students_delete(student_id):
    student = db_query("SELECT User_ID FROM Student WHERE Student_ID = %s", 
                       (student_id,), fetchone=True)
    
    if not student:
        logging.warning(f"Attempted delete of non-existent student {student_id}")
        return jsonify({"ok": False, "error": "Student not found"}), 404
    
    logging.info(f"Deleting student {student_id} with User_ID {student.get('User_ID')}")
    
    db_query("DELETE FROM Student WHERE Student_ID = %s", (student_id,), commit=True)
    
    if student.get("User_ID"):
        logging.info(f"Deleting user account {student['User_ID']}")
        db_query("DELETE FROM Users WHERE User_ID = %s", (student["User_ID"],), commit=True)
    
    logging.info(f"Successfully deleted student {student_id}")
    return jsonify({"ok": True, "message": "Student and login account deleted."})
```

### Track Who Deleted
```python
if not session.get("user"):
    return jsonify({"ok": False, "error": "Not authenticated"}), 401

admin_id = session["user"]["id"]
logging.info(f"Admin {admin_id} deleted student {student_id}")
```

## Transaction Consistency

### Both or Nothing
```python
with db_cursor() as (db, cursor):
    cursor.execute("DELETE FROM Student WHERE Student_ID = %s", (student_id,))
    
    if student and student.get("User_ID"):
        cursor.execute("DELETE FROM Users WHERE User_ID = %s", (student["User_ID"],))
    
    db.commit()  # Both succeed or both fail
```

Current implementation: Commits each separately (risky).

**Better**: Use single transaction for atomicity.

## Related Deletions

### Delete Employee
```sql
SELECT User_ID FROM Employee WHERE Emp_ID = %s
DELETE FROM Employee WHERE Emp_ID = %s  -- Cascades to Instructor, Teaches
DELETE FROM Users WHERE User_ID = %s
```

### Delete Department
```sql
DELETE FROM Department WHERE Dept_ID = %s  -- Fails if employees in dept
-- OR with cascade:
DELETE FROM Department WHERE Dept_ID = %s  -- All employees deleted
```

### Delete Subject
```sql
DELETE FROM Subject WHERE Subject_ID = %s  -- Cascades to Studies, Teaches
```

## Rollback Scenario

### If Error During Deletion
```python
try:
    db_query("DELETE FROM Student WHERE Student_ID = %s", (student_id,), commit=True)
    if student and student.get("User_ID"):
        db_query("DELETE FROM Users WHERE User_ID = %s", (student["User_ID"],), commit=True)
except Exception as e:
    logging.error(f"Error deleting student: {e}")
    return jsonify({"ok": False, "error": "Deletion failed"}), 500
```

**Current issue**: First delete succeeds, then error on user delete
- Student deleted, but user account remains
- Orphaned user account

**Solution**: Use single transaction (see above).

## Testing

### Manual Test
```sql
-- Create test data
INSERT INTO Student VALUES (99999, 'Test', 'Student', NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO Users VALUES (NULL, 'Test User', 'test@test.com', '$2b$12$...', 'student', NOW());
UPDATE Student SET User_ID = LAST_INSERT_ID() WHERE Student_ID = 99999;

-- Verify exists
SELECT * FROM Student WHERE Student_ID = 99999;
SELECT * FROM Users WHERE User_ID = (SELECT User_ID FROM Student WHERE Student_ID = 99999);

-- Delete
DELETE FROM Student WHERE Student_ID = 99999;

-- Verify gone
SELECT * FROM Student WHERE Student_ID = 99999;  -- No results
SELECT * FROM Users WHERE Email='test@test.com';  -- No results
```

## Summary

- **Purpose**: Remove student and all related data
- **Steps**: Lookup → Delete student → Delete user (conditional)
- **Cascade**: Automatic for Studies table
- **Risk**: User account left behind if not deleted
- **Better**: Transaction for atomicity
- **Best**: Soft delete for recoverability
- **Performance**: Fast; <10ms typically
- **Safety**: Always use WHERE clause with specific condition
