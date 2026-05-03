# SQL Query: Find User by Email (Signin)

## Query
```sql
SELECT * FROM Users WHERE Email = %s
```

## Location
`/api/signin` endpoint - `api_signin()` function

## Purpose
Retrieves user account information by email during login authentication.

## Parameters
- `%s` (placeholder): Email address to search for (e.g., "john@school.com")

## How It Works
1. **Query execution**: Searches the Users table for a record matching the provided email
2. **Result**: Returns all columns from the Users table if found
3. **Security**: Uses parameterized query (%s placeholder) to prevent SQL injection

## Database Columns Returned
```
User_ID          - Primary key, unique identifier for the user
Full_Name        - User's full name
Email            - Email address (unique)
Password_Hash    - Bcrypt hashed password
Role             - User role: 'student', 'teacher', or 'admin'
Created_At       - Timestamp when account was created
```

## Example Usage
```python
user = db_query(
    "SELECT * FROM Users WHERE Email = %s",
    ("student@school.com",),  # Parameters as tuple
    fetchone=True
)
```

## Expected Results

### Successful Match (User Exists)
```json
{
  "User_ID": 5,
  "Full_Name": "John Doe",
  "Email": "john@school.com",
  "Password_Hash": "$2b$12$...",
  "Role": "student",
  "Created_At": "2026-01-15 10:30:00"
}
```

### No Match
```python
user = None  # db_query returns None if no results
```

## Why This Query Pattern?

### Security Considerations
1. **Parameterized Query**: The `%s` placeholder prevents SQL injection
   - Safe: `"SELECT * FROM Users WHERE Email = %s"`
   - Unsafe: `f"SELECT * FROM Users WHERE Email = '{email}'"`

2. **Email Case Handling**: Frontend should normalize email to lowercase before sending
   - The WHERE clause is case-sensitive by default in MySQL
   - Database could have index on Email column for faster lookup

3. **Timing Attacks**: Password verification happens AFTER this query returns
   - If user doesn't exist, error is returned immediately
   - Could allow attackers to enumerate valid emails
   - **Mitigation**: Some systems use consistent response time

## Performance Optimization

### Current Performance
```
- Without index: O(n) - full table scan
- With index: O(log n) - index lookup
```

### Recommended Index
```sql
CREATE UNIQUE INDEX idx_users_email ON Users(Email);
```

### Why This Index?
- Emails should be unique (prevents duplicate accounts)
- Lookup by email is very common (signin, password reset, etc.)
- UNIQUE constraint also prevents duplicates at database level
- Converts O(n) scan to O(log n) lookup

## Related Signup Query
During signup, the application inserts a new Users record:
```sql
INSERT INTO Users (Full_Name, Email, Password_Hash, Role)
VALUES (%s, %s, %s, %s)
```

## Flow in Signin Process
```
1. User submits email + password
2. SELECT * FROM Users WHERE Email = %s  <- This query
3. If found: Compare password hash
4. If matches: Fetch linked Student/Employee record
5. Create session
6. Return user data
```

## Error Handling
```python
if not user:
    return jsonify({"ok": False, "error": "User not found"}), 404

if not check_password_hash(user["Password_Hash"], password):
    return jsonify({"ok": False, "error": "Wrong password"}), 401
```

## Alternative Query Patterns

### Select Specific Columns (More Efficient)
```sql
SELECT User_ID, Full_Name, Email, Password_Hash, Role 
FROM Users 
WHERE Email = %s
```

### Select with Role Filter (Constrained Signin)
```sql
SELECT * FROM Users 
WHERE Email = %s AND Role = %s
```

---

# Security Deep Dive

## Why Passwords Are Stored as Hashes
- **Original password**: Never stored in database
- **Hash function**: One-way function (SHA-256, bcrypt, Argon2)
- **Hash verification**: `check_password_hash()` compares provided password to stored hash
- **Even if DB is hacked**: Attacker cannot recover plaintext passwords

## Email Normalization
```python
email = data.get("email", "").strip().lower()
```
- **Strip**: Removes whitespace
- **Lower**: Converts to lowercase (prevents case sensitivity issues)
- **Index optimization**: Consistent format improves index effectiveness

## Why This Query Happens First
1. Check if user exists (fail fast if not)
2. Get password hash for verification
3. Get user role for role-specific logic
4. Everything in one query (efficient)

---

# Common Variations

### Get User by User_ID
```sql
SELECT * FROM Users WHERE User_ID = %s
```

### Get User with Email Hint
```sql
SELECT * FROM Users WHERE Email LIKE %s
```

### Get All Admins
```sql
SELECT * FROM Users WHERE Role = 'admin'
```

### Get Users Created in Date Range
```sql
SELECT * FROM Users 
WHERE Created_At BETWEEN %s AND %s
ORDER BY Created_At DESC
```

---

# SQL Injection Example (WHY WE DON'T DO THIS)

### Vulnerable Code
```python
# WRONG - NEVER DO THIS
email = request.get_json().get("email")
query = f"SELECT * FROM Users WHERE Email = '{email}'"
```

### Attack Example
```
Input: " OR "1"="1
Query becomes: SELECT * FROM Users WHERE Email = "" OR "1"="1"
Result: Returns ALL users (bypasses authentication)
```

### Protected Code
```python
# CORRECT - Use parameterized queries
query = "SELECT * FROM Users WHERE Email = %s"
db_query(query, (email,), fetchone=True)
```

---

# Index Statistics

### Query Cost Without Index
- Table Scan: O(n) where n = total users
- Example: 10,000 users × 50 bytes = 500KB scan every login
- CPU cost: High (must check every row)
- I/O cost: High (may read multiple disk blocks)

### Query Cost With Index
- Index Lookup: O(log n)
- Example: Binary search through 10,000 users = ~13 comparisons
- CPU cost: Low
- I/O cost: Low (1-2 disk reads typically)

### Expected Execution Plan
```
id | select_type | table | type  | rows | key
1  | SIMPLE      | Users | const | 1    | idx_users_email
```

The "const" type means constant-time lookup via unique index.
