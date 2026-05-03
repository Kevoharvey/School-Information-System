# SQL Query: Get Student Entity from User_ID

## Query
```sql
SELECT Student_ID, Fname, Lname FROM Student WHERE User_ID = %s
```

## Location
`/api/signin` endpoint - `api_signin()` function (Student role branch)

## Purpose
Retrieves the linked Student record after successfully authenticating a user account. Maps from the Users table to the Student table.

## Parameters
- `%s` (placeholder): User_ID from the Users table

## How It Works
1. **Input**: User_ID obtained from successful password verification
2. **Lookup**: Finds the Student record linked to that user account
3. **Result**: Returns student identification and name fields
4. **Validation**: If no Student record found, returns 404 error

## Why Two Tables?
**Database Design Pattern**: Separation of concerns
```
Users table (login/auth)
├── User_ID (primary key)
├── Email (unique, used for login)
├── Password_Hash
└── Role

Student table (student data)
├── Student_ID (primary key)
├── User_ID (foreign key linking to Users)
├── Fname
├── Lname
└── [other student fields]
```

## Example Usage
```python
# After password verification
user = db_query("SELECT * FROM Users WHERE Email = %s", (email,), fetchone=True)

# Get linked student record
entity = db_query(
    "SELECT Student_ID, Fname, Lname FROM Student WHERE User_ID = %s",
    (user["User_ID"],),
    fetchone=True
)
```

## Expected Results

### Successful Match
```json
{
  "Student_ID": 12345,
  "Fname": "John",
  "Lname": "Doe"
}
```

### No Matching Student
```python
entity = None  # Student not linked to this user account
```

## Flow in Complete Signin
```
Step 1: User submits email + password
Step 2: SELECT * FROM Users WHERE Email = %s
Step 3: verify password_hash (Python code)
Step 4: If student role, run THIS query
Step 5: SELECT Student_ID, Fname, Lname FROM Student WHERE User_ID = %s
Step 6: Create session with Student_ID (not User_ID!)
Step 7: Return student data to frontend
```

## Critical Difference: Student_ID vs User_ID

### Session Uses Student_ID
```python
session["user"] = {
    "id": entity["Student_ID"],  # NOT user["User_ID"]
    "name": f"{entity['Fname']} {entity['Lname']}",
    "role": "student"
}
```

### Why This Design?
- **User_ID**: Internal authentication ID (hidden from students)
- **Student_ID**: Visible student identifier (used in URLs, forms)
- **Separation**: Frontend uses Student_ID, backend tracks User_ID internally

### Example
```
User account: User_ID = 523
Student record: Student_ID = 12345
Login session: Contains Student_ID = 12345
URL in frontend: /api/students/12345
Database query: Uses User_ID = 523 for internal lookup
```

## Error Handling

### Student Not Linked Error
```python
if not entity:
    return jsonify({"ok": False, "error": "Student not linked"}), 500
```

This 500 error indicates:
- User account exists (auth successful)
- BUT no corresponding Student record found
- Data integrity issue (should be prevented at signup time)

## Related Signup Query
During student signup, both records are created together:

```sql
INSERT INTO Users (Full_Name, Email, Password_Hash, Role)
VALUES (%s, %s, %s, %s)

INSERT INTO Student (Student_ID, Fname, Lname, Student_Email, User_ID)
VALUES (%s, %s, %s, %s, %s)  -- Uses User_ID from first insert
```

## Index Optimization

### Recommended Index
```sql
CREATE INDEX idx_student_user_id ON Student(User_ID);
```

### Why?
- Foreign key lookups are very common
- Signin happens frequently (every session)
- Converts O(n) scan to O(log n) lookup

### Query Execution Plan
```
id | select_type | table   | type | rows | key
1  | SIMPLE      | Student | ref  | 1    | idx_student_user_id
```

## Data Consistency Check

### Find Orphaned Users
Users with no linked Student (data integrity issue):
```sql
SELECT u.User_ID, u.Email, u.Role
FROM Users u
LEFT JOIN Student s ON u.User_ID = s.User_ID
WHERE u.Role = 'student' AND s.Student_ID IS NULL
```

### Find Orphaned Students
Students with no linked User (shouldn't happen):
```sql
SELECT st.Student_ID, st.Fname, st.Lname
FROM Student st
LEFT JOIN Users u ON st.User_ID = u.User_ID
WHERE st.User_ID IS NOT NULL AND u.User_ID IS NULL
```

## Comparison: Student vs Teacher vs Admin

### Student Role
```sql
SELECT Student_ID, Fname, Lname FROM Student WHERE User_ID = %s
```
- Links to Student table
- Session uses Student_ID

### Teacher Role
```sql
SELECT Emp_ID, Emp_FName, Emp_Lname FROM Employee WHERE User_ID = %s
```
- Links to Employee table
- Session uses Emp_ID

### Admin Role
No additional lookup needed:
```python
session["user"] = {
    "id": user["User_ID"],  # Uses User_ID directly
    "name": user["Full_Name"],
    "role": "admin"
}
```

## Selected Columns Strategy

### This Query (Minimal Columns)
```sql
SELECT Student_ID, Fname, Lname FROM Student WHERE User_ID = %s
```
- Only retrieves needed columns
- Reduces network transfer
- Faster query execution

### Alternative (All Columns)
```sql
SELECT * FROM Student WHERE User_ID = %s
```
- Retrieves everything (inefficient)
- Should use this only for admin viewing student details

## Usage in Frontend

### Student Session
```javascript
// After successful signin
const response = await fetch('/api/me');
const data = await response.json();
console.log(data.user.id);  // Student_ID = 12345
console.log(data.user.name); // "John Doe"
console.log(data.user.role); // "student"

// Use Student_ID in API calls
const grades = await fetch(`/api/students/${data.user.id}/grades`);
```

## Security Considerations

### Why Only SELECT (Read-Only)?
- Signin process only reads data
- No modifications during authentication
- If query fails, entire signin fails
- No partial state created

### User Can't Change This
- A user's Student_ID links to their User account
- Student_ID is assigned at signup
- User_ID is auto-generated
- User cannot modify this relationship

### Audit Trail
- Each signin attempt uses this query
- Can be logged for security monitoring
- Helps detect unauthorized access attempts

## Performance Metrics

### Query Complexity
- **Type**: Equality lookup (WHERE clause with =)
- **Tables**: 1 table scanned
- **Joins**: 0 joins
- **Sorting**: None

### Estimated Performance
```
Without index: ~5-10ms (for 100,000 students)
With index: ~1-2ms (constant time)
Network roundtrip: ~10-50ms (varies by network)
Total: ~50-60ms for this query alone
```

---

# Complete Signin Flow

```
User Entry → Validation → User Lookup → Password Check → Entity Lookup → Session → Response
              (Python)      (THIS QUERY)  (Python hash)   (THIS QUERY)    (Python) (JSON)
```

This query is crucial because:
1. Determines which student they are
2. Gets their display name
3. Links auth (User) to business data (Student)
4. Enables all subsequent student-specific queries
