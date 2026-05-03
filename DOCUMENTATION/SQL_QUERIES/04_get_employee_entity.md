# SQL Query: Get Employee Entity from User_ID

## Query
```sql
SELECT Emp_ID, Emp_FName, Emp_Lname FROM Employee WHERE User_ID = %s
```

## Location
`/api/signin` endpoint - `api_signin()` function (Teacher/Employee role branch)

## Purpose
Retrieves the linked Employee record after successful authentication. Used for teacher and other employee roles to map from Users table to Employee table.

## Parameters
- `%s` (placeholder): User_ID from the Users table

## How It Works
1. **Input**: User_ID obtained from successful password verification
2. **Lookup**: Finds the Employee record linked to that user account
3. **Result**: Returns employee ID and full name
4. **Validation**: If no Employee record found, returns 500 error
5. **Session**: Uses Emp_ID (not User_ID) for subsequent requests

## Database Relationship

```
Users (Authentication)          Employee (Business Data)
├── User_ID (PK)          <─── User_ID (FK)
├── Email                      ├── Emp_ID (PK)
├── Password_Hash              ├── Emp_FName
├── Role (employee/teacher)    ├── Emp_Lname
└── Full_Name                  └── [other employee data]
```

## Example Usage in Signin

```python
# After password verification confirms user is a teacher/employee
user = db_query("SELECT * FROM Users WHERE Email = %s", (email,), fetchone=True)

# Get linked employee record (THIS QUERY)
entity = db_query(
    "SELECT Emp_ID, Emp_FName, Emp_Lname FROM Employee WHERE User_ID = %s",
    (user["User_ID"],),
    fetchone=True
)

# Create session with Emp_ID
session["user"] = {
    "id": entity["Emp_ID"],  # Employee ID, not User_ID
    "name": f"{entity['Emp_FName']} {entity['Emp_Lname']}",
    "role": user["Role"]  # "teacher" or other employee role
}
```

## Expected Results

### Successful Match (Employee Exists)
```json
{
  "Emp_ID": 567,
  "Emp_FName": "Jane",
  "Emp_Lname": "Smith"
}
```

### No Matching Employee
```python
entity = None
# Returns error: "Employee not linked"
```

## Difference from Student Query

### Student Role
```sql
SELECT Student_ID, Fname, Lname FROM Student WHERE User_ID = %s
```

### Employee Role
```sql
SELECT Emp_ID, Emp_FName, Emp_Lname FROM Employee WHERE User_ID = %s
```

### Similarities
- Both link from Users to role-specific table
- Both use User_ID as foreign key
- Both return entity ID and names
- Both used during signin

### Differences
| Aspect | Student | Employee |
|--------|---------|----------|
| ID Field | Student_ID | Emp_ID |
| First Name | Fname | Emp_FName |
| Last Name | Lname | Emp_Lname |
| Related Roles | student only | teacher, admin staff, etc. |
| Employee Table | Only Student | Employee + Instructor |

## Employee Roles Using This Query

This query is used for ANY non-student role:

### Teacher (Instructor)
```python
# User.Role = "teacher"
entity = db_query(
    "SELECT Emp_ID, Emp_FName, Emp_Lname FROM Employee WHERE User_ID = %s",
    (user["User_ID"],)
)
# Also linked to Instructor table
```

### Other Staff Roles
```python
# User.Role = "admin_staff", "counselor", etc.
entity = db_query(
    "SELECT Emp_ID, Emp_FName, Emp_Lname FROM Employee WHERE User_ID = %s",
    (user["User_ID"],)
)
# Only in Employee table (not Instructor)
```

## Complete Employee Signup Flow

During teacher signup, THREE records are created:

```python
# Step 1: Create Users record
INSERT INTO Users (Full_Name, Email, Password_Hash, Role)
VALUES ('Jane Smith', 'jane@school.com', '$2b$12$...', 'teacher')
# Returns: user_id = 100

# Step 2: Create Employee record
INSERT INTO Employee (Emp_ID, Emp_FName, Emp_Lname, Dept_ID, User_ID)
VALUES (567, 'Jane', 'Smith', 3, 100)  # Links to User_ID 100

# Step 3: Create Instructor record
INSERT INTO Instructor (Emp_ID)
VALUES (567)  # Links to Emp_ID 567
```

This query retrieves the connection from step 2.

## Index Optimization

### Recommended Index
```sql
CREATE INDEX idx_employee_user_id ON Employee(User_ID);
```

### Why This Index?
- Employee lookup by User_ID happens during every teacher/staff signin
- Without index: O(n) full table scan
- With index: O(log n) or O(1) for small tables

### Query Execution Plan (With Index)
```
id | select_type | table    | type | rows | key
1  | SIMPLE      | Employee | ref  | 1    | idx_employee_user_id
```

### Performance Improvement
```
Without index: 20-50ms (may scan entire Employee table)
With index: 1-3ms (direct lookup)
Improvement: ~10-30x faster
```

## Error Handling

### Employee Not Linked
```python
if not entity:
    return jsonify({
        "ok": False, 
        "error": "Employee not linked"
    }), 500
```

**Meaning**:
- Users record exists (email found, password verified)
- Employee record missing
- Data integrity issue (shouldn't happen after successful signup)

**Possible Causes**:
1. Employee record was deleted but User account remained
2. Database corruption
3. Incomplete signup process (transaction rollback)

## Data Consistency Checks

### Find Orphaned Employee Users
Users with no linked Employee record:
```sql
SELECT u.User_ID, u.Email, u.Role, u.Full_Name
FROM Users u
LEFT JOIN Employee e ON u.User_ID = e.User_ID
WHERE u.Role IN ('teacher', 'staff') AND e.Emp_ID IS NULL
```

### Find Orphaned Employees
Employee records with no linked User:
```sql
SELECT e.Emp_ID, e.Emp_FName, e.Emp_Lname
FROM Employee e
LEFT JOIN Users u ON e.User_ID = u.User_ID
WHERE e.User_ID IS NOT NULL AND u.User_ID IS NULL
```

## Related Queries

### Find All Employees
```sql
SELECT * FROM Employee
```

### Get Employee with Department
```sql
SELECT e.*, d.Dept_Name 
FROM Employee e
JOIN Department d ON e.Dept_ID = d.Dept_ID
WHERE e.User_ID = %s
```

### Get Teacher-Specific Info
```sql
SELECT e.Emp_ID, e.Emp_FName, e.Emp_Lname, i.Qualification
FROM Employee e
JOIN Instructor i ON e.Emp_ID = i.Emp_ID
WHERE e.User_ID = %s
```

## Session ID Implications

### Session Contains Emp_ID
```javascript
// After teacher signin
session.user = {
  id: 567,  // Emp_ID from Employee table
  name: "Jane Smith",
  role: "teacher"
}
```

### All Teacher Endpoints Use Emp_ID
```
GET /api/teacher/567/subjects
GET /api/teacher/567/students
POST /api/teaches  -- requires emp_id = 567
PUT /api/instructors/567
DELETE /api/instructors/567
```

### Never Uses User_ID in Frontend
```
WRONG: GET /api/teacher/100  -- User_ID
CORRECT: GET /api/teacher/567  -- Emp_ID
```

## Multi-Role Employees

### Can Employee Be Multiple Roles?
Technically yes, by having:
```sql
SELECT Role FROM Users WHERE Email = 'person@school.com'
-- Returns: "teacher"
```

But User.Role is single value, so each User_ID has ONE role.

### If Need Multiple Roles
Design pattern would be:
```
Users <- User_ID -> Employee <- Emp_ID -> Instructor (for teaching)
                             <- Emp_ID -> [Other role tables]
```

Current system: One role per user account.

## Performance Metrics

### Query Characteristics
- **Operation**: Equality lookup (WHERE User_ID = ?)
- **Tables**: 1 table (Employee)
- **Joins**: 0
- **Sorting**: None
- **Aggregation**: None

### Performance Expectations
```
Scenario: 1000 employees in database

Without index:
  - Time: 15-25ms
  - Operations: Average 500 rows scanned
  - I/O: Multiple disk reads possible

With index (recommended):
  - Time: 1-2ms
  - Operations: Index lookup (log n)
  - I/O: 1-2 disk reads
```

## Why User_ID and Emp_ID Are Different

### User_ID (Authentication)
- Used for login
- Private to backend
- Not exposed in URLs typically
- Auto-generated by Users table

### Emp_ID (Business Data)
- Used in faculty lists, directories
- Visible in application UI
- Exposed in URLs/API
- May be meaningful ID (like employee number)

### Example
```
User creates account with email: jane.smith@school.com
User_ID assigned: 8847 (auto-increment)
Emp_ID provided: 567 (existing employee record)

Frontend shows: "Teacher Jane Smith (567)"
Backend tracks: User_ID 8847 for auth
```

## Conclusion

This query is essential for:
1. **Signin completion**: Maps user auth to employee business data
2. **Session creation**: Stores Emp_ID for subsequent requests
3. **Data linking**: Bridges authentication and operational data
4. **Role differentiation**: Different from student signin flow
5. **Multi-role support**: Same pattern used for all non-student roles
