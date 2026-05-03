# SQL Query: Insert New Student

## Query
```sql
INSERT INTO Student
  (Student_ID, Fname, Lname, Level, Birth_Date, Student_Email, City, Street, Building_Num)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
```

## Location
`/api/students` endpoint (POST) - `api_students_add()` function

## Purpose
Creates a new student record in the database. Used by administrators to add students to the system.

## Parameters
- `Student_ID`: Unique identifier for the student
- `Fname`: First name
- `Lname`: Last name
- `Level`: Academic level/grade
- `Birth_Date`: Date of birth (nullable)
- `Student_Email`: Email address (nullable)
- `City`: City of residence (nullable)
- `Street`: Street address (nullable)
- `Building_Num`: Building number (nullable)

## How It Works

```python
@app.route("/api/students", methods=["POST"])
def api_students_add():
    d = request.get_json(silent=True) or {}
    try:
        db_query(
            """INSERT INTO Student
               (Student_ID, Fname, Lname, Level, Birth_Date, Student_Email, City, Street, Building_Num)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (d["student_id"], d["fname"], d["lname"],
             d.get("level") or None, d.get("birth_date") or None,
             d.get("email") or None, d.get("city") or None,
             d.get("street") or None, d.get("building_num") or None),
            commit=True
        )
    except mysql.connector.IntegrityError as e:
        return jsonify({"ok": False, "error": str(e)}), 409
    return jsonify({"ok": True, "message": "Student added!"})
```

## Required vs Optional Fields

### Required
- `Student_ID`: Primary key (unique, cannot be NULL)
- `Fname`: First name
- `Lname`: Last name

### Optional (Can Be NULL)
- `Level`: Academic level
- `Birth_Date`: Date of birth
- `Student_Email`: Contact email
- `City`: Home city
- `Street`: Street address
- `Building_Num`: Building number

## Input Processing

### Handling Optional Fields
```python
d.get("level") or None  # Returns None if not provided or empty string

# More explicitly:
level = d.get("level")
if not level:
    level = None
```

### This Pattern
- Allows optional fields to be omitted from request
- Converts empty strings to NULL
- Prevents empty strings in database (uses NULL instead)

## Request Format

### Example Request
```json
{
  "student_id": 10001,
  "fname": "John",
  "lname": "Doe",
  "level": 1,
  "birth_date": "2007-05-15",
  "email": "john.doe@school.com",
  "city": "New York",
  "street": "123 Main Street",
  "building_num": 5
}
```

### Minimal Request (Only Required)
```json
{
  "student_id": 10002,
  "fname": "Jane",
  "lname": "Smith"
}
```

## INSERT Statement Mechanics

### Column Order
```sql
INSERT INTO Student
  (Student_ID, Fname, Lname, Level, Birth_Date, Student_Email, City, Street, Building_Num)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
```

- Column names specified explicitly (best practice)
- Values must match column order
- Explicitly listed columns are best; no ambiguity

### Alternative (Less Safe)
```sql
-- NOT RECOMMENDED
INSERT INTO Student VALUES (%s, %s, %s, %s, %s, %s, %s, %s, ...)
-- Depends on exact column order; breaks if schema changes
```

## Database Constraints

### Primary Key Constraint
```sql
PRIMARY KEY (Student_ID)
```

**Violation**: If Student_ID already exists
```json
{
  "ok": false,
  "error": "Duplicate entry '10001' for key 'PRIMARY'"
}
```

HTTP Status: **409 Conflict**

### Data Type Constraints
```sql
-- Stored as DATE type; must be valid date format
Birth_Date DATE

-- VARCHAR types; no length violations checked in code
Fname VARCHAR(100)
```

**Validation**: Handled by MySQL driver
- Invalid date format: Causes error
- String too long: May truncate or error

## Error Handling

```python
except mysql.connector.IntegrityError as e:
    return jsonify({"ok": False, "error": str(e)}), 409
```

### Integrity Error Cases
1. **Duplicate Student_ID**: Primary key violation
2. **Foreign key violation**: If Level references Department and doesn't exist
3. **Unique constraint violation**: If another unique constraint exists
4. **NOT NULL violation**: If required column has no value

### Returns HTTP 409 (Conflict)
Appropriate status for resource already existing.

## Parameterized Query Safety

### SQL Injection Attack Example
```python
# WRONG - Vulnerable
student_id = input("Enter ID: ")  # "'; DROP TABLE Student; --"
query = f"INSERT INTO Student VALUES ({student_id}, ...)"
```

### Protected Version
```python
# CORRECT - Safe
query = "INSERT INTO Student VALUES (%s, ...)"
db_query(query, (student_id, ...), commit=True)
```

The `%s` placeholder and separate params prevent injection.

## Commit Behavior

```python
db_query(..., commit=True)
```

**What happens**:
1. INSERT executes
2. If successful: `db.commit()` is called
3. Changes persist permanently in database
4. Other connections can see new row
5. If error: Transaction rollback (no partial data)

**Without commit**:
- Changes would be in transaction buffer
- Only visible to current connection
- Other connections won't see new row until commit

## Performance Characteristics

### Single Insert
- Time: 1-5ms typically
- I/O: 1 write operation
- Indexes: Updates all indexes on Student table

### Batch Insert (More Efficient)
```sql
INSERT INTO Student VALUES 
  (%s, %s, %s, ...),
  (%s, %s, %s, ...),
  (%s, %s, %s, ...)
```

**Benefit**: Single statement, multiple rows
- Time: 3-15ms for 1000 rows
- vs 1000 separate queries: 1000-5000ms

### With Indexes
```sql
-- Indexes that get updated:
CREATE UNIQUE INDEX idx_student_id ON Student(Student_ID);  -- Updated
CREATE INDEX idx_fname_lname ON Student(Fname, Lname);       -- Updated
```

Each index adds overhead; more indexes = slower inserts.

## Practical Example

### Frontend Form
```html
<form onsubmit="addStudent(event)">
  <input name="student_id" type="number" required>
  <input name="fname" required>
  <input name="lname" required>
  <input name="level" type="number">
  <input name="birth_date" type="date">
  <input name="email" type="email">
  <input name="city">
  <input name="street">
  <input name="building_num" type="number">
  <button>Add Student</button>
</form>
```

### JavaScript Handler
```javascript
async function addStudent(event) {
  event.preventDefault();
  const formData = new FormData(event.target);
  const data = Object.fromEntries(formData);
  
  const response = await fetch('/api/students', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  
  const result = await response.json();
  if (result.ok) {
    alert('Student added!');
    event.target.reset();
  } else {
    alert('Error: ' + result.error);
  }
}
```

## Data Validation

### Backend Validation
Current code has MINIMAL validation:
- Checks that required fields provided
- Type coercion (convert empty to NULL)

### Recommended Additional Validation
```python
# Check Student_ID is positive
if d["student_id"] < 0:
    return jsonify({"ok": False, "error": "Invalid student ID"}), 400

# Validate birth date
from datetime import datetime
if d.get("birth_date"):
    try:
        datetime.strptime(d["birth_date"], "%Y-%m-%d")
    except ValueError:
        return jsonify({"ok": False, "error": "Invalid date format"}), 400

# Check name length
if len(d["fname"]) > 100:
    return jsonify({"ok": False, "error": "Name too long"}), 400

# Validate email format
import re
if d.get("email") and not re.match(r"[^@]+@[^@]+\.[^@]+", d["email"]):
    return jsonify({"ok": False, "error": "Invalid email"}), 400
```

## Related Operations

### Create Student with User Account
During signup, student record is created WITH user account:
```sql
INSERT INTO Users (Full_Name, Email, Password_Hash, Role)
VALUES ('John Doe', 'john@school.com', '$2b$12$...', 'student')

INSERT INTO Student (Student_ID, Fname, Lname, Student_Email, User_ID)
VALUES (10001, 'John', 'Doe', 'john@school.com', @user_id)
```

### Separate: Adding Student Without Login
This endpoint creates ONLY Student record:
- For pre-registration
- For bulk import
- For students without system login yet

## Transaction Safety

### Multi-Step Signup (Protected)
```python
with db_cursor() as (db, cursor):
    # Step 1: Create User
    cursor.execute("INSERT INTO Users ...")
    user_id = cursor.lastrowid
    
    # Step 2: Create Student
    cursor.execute("INSERT INTO Student ...", (..., user_id))
    
    # Step 3: Commit both or rollback
    db.commit()  # Both succeed or both fail
```

### Single Insert (Automatic)
```python
# This endpoint: just insert one record
db_query(..., commit=True)
```

Either succeeds completely or fails completely.

## Audit Trail

### Add Logging
```python
import logging

def api_students_add():
    d = request.get_json(silent=True) or {}
    try:
        db_query(..., commit=True)
        logging.info(f"Added student: {d['student_id']} {d['fname']} {d['lname']}")
        return jsonify({"ok": True, "message": "Student added!"})
    except mysql.connector.IntegrityError as e:
        logging.warning(f"Failed to add student: {str(e)}")
        return jsonify({"ok": False, "error": str(e)}), 409
```

### Track Who Added Student
```python
# Requires authenticated session
if not session.get("user"):
    return jsonify({"ok": False, "error": "Not authenticated"}), 401

admin_id = session["user"]["id"]
logging.info(f"Admin {admin_id} added student {d['student_id']}")
```

## Related Queries

### Add Multiple Students (Bulk)
```sql
INSERT INTO Student VALUES 
  (10001, 'John', 'Doe', 1, '2007-05-15', ...),
  (10002, 'Jane', 'Smith', 1, '2008-03-20', ...),
  (10003, 'Bob', 'Jones', 2, '2006-11-10', ...)
```

### Add with Default Values
```sql
INSERT INTO Student (Student_ID, Fname, Lname, Level) 
VALUES (%s, %s, %s, 1)  -- Level defaults to 1
```

### Check Before Insert
```sql
-- Prevent duplicates
INSERT IGNORE INTO Student ...  -- Silently ignores duplicates
-- OR
INSERT ... ON DUPLICATE KEY UPDATE ...  -- Updates if exists
```

## Summary

- **Purpose**: Add new student to system
- **Required**: Student_ID, Fname, Lname
- **Optional**: Birth date, email, address, level
- **Error**: 409 if Student_ID duplicate
- **Safety**: Parameterized query prevents injection
- **Performance**: Fast; should be < 5ms
- **Validation**: Minimal in code; add more if needed
