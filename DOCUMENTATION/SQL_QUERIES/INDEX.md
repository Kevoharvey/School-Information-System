# SQL Queries Index & Summary

Complete documentation of all SQL queries in the School Information System backend.

## Quick Navigation

### By Category

#### Authentication & Session
- [01 - Health Check](./01_health_check.md) - Database connectivity test
- [02 - Find User by Email](./02_signin_user_lookup.md) - User authentication lookup
- [03 - Get Student Entity](./03_get_student_entity.md) - Link from User to Student
- [04 - Get Employee Entity](./04_get_employee_entity.md) - Link from User to Employee

#### Statistics & Counting
- [05 - Count Records](./05_count_records.md) - Dashboard statistics

#### Student Management
- [06 - List Students](./06_list_students.md) - List all students with calculated age
- [07 - Insert Student](./07_insert_student.md) - Add new student record
- [08 - Update Student](./08_update_student.md) - Modify student information
- [09 - Delete Student](./09_delete_student.md) - Remove student with cascade

#### Grade Management
- [10 - Upsert Grade](./10_upsert_grade.md) - Insert or update student grade

#### Teacher Operations
- [11 - Teacher Subject Students](./11_teacher_subject_students.md) - Students in specific subject with grades
- [12 - Teacher All Students](./12_teacher_all_students.md) - All students across all teacher's subjects

## Query Summary Table

| File | Query Type | Purpose | Complexity | Performance |
|------|-----------|---------|-----------|-------------|
| 01 | SELECT | Health check | Very Low | <1ms |
| 02 | SELECT | User lookup by email | Low | 1-2ms |
| 03 | SELECT | Get student ID from user | Low | 1-2ms |
| 04 | SELECT | Get employee ID from user | Low | 1-2ms |
| 05 | SELECT | Count multiple tables | Low | 20-50ms |
| 06 | SELECT | List students with age calc | Medium | 5-20ms |
| 07 | INSERT | Add student | Low | 1-5ms |
| 08 | UPDATE | Modify student | Low | 1-5ms |
| 09 | DELETE | Delete student with cascade | Medium | 3-9ms |
| 10 | INSERT/UPDATE | Upsert grade | Low | 2-5ms |
| 11 | SELECT | Class roster with grades | Medium | 5-15ms |
| 12 | SELECT | All students with DISTINCT | Medium | 5-20ms |

## Queries by Database Operation

### SELECT (Read) Operations
**Most Common Operations**

#### Simple Lookups
```
01. Health Check               SELECT 1
02. Find User by Email         SELECT * FROM Users WHERE Email = ?
03. Get Student Entity         SELECT * FROM Student WHERE User_ID = ?
04. Get Employee Entity        SELECT * FROM Employee WHERE User_ID = ?
```

#### Counting & Aggregation
```
05. Count Records              SELECT COUNT(*) from multiple tables
```

#### Listing & Complex Reads
```
06. List Students              SELECT with JOIN and TIMESTAMPDIFF
11. Teacher Subject Students   SELECT with multiple JOINs
12. Teacher All Students       SELECT DISTINCT with JOINs
```

### INSERT (Create) Operations
```
07. Add Student                INSERT INTO Student
10. Upsert Grade               INSERT ... ON DUPLICATE KEY UPDATE
```

### UPDATE (Modify) Operations
```
08. Update Student             UPDATE Student SET
```

### DELETE (Remove) Operations
```
09. Delete Student             DELETE FROM Student + DELETE FROM Users
```

## Transaction Types

### Single Statement (No Transaction)
- 02 - Find User
- 03 - Get Student Entity  
- 04 - Get Employee Entity
- 05 - Count Records
- 06 - List Students
- 11 - Teacher Subject Students
- 12 - Teacher All Students

### Single Statement with Commit
- 01 - Health Check (read-only)
- 07 - Insert Student (commit=True)
- 08 - Update Student (commit=True)
- 10 - Upsert Grade (commit=True)

### Multi-Statement Transaction
- 09 - Delete Student (two separate commits, should be one transaction)

## Indexes Needed

### Critical Indexes (Performance)
```sql
-- Users table
CREATE UNIQUE INDEX idx_users_email ON Users(Email);

-- Student table
CREATE INDEX idx_student_user_id ON Student(User_ID);

-- Employee table  
CREATE INDEX idx_employee_user_id ON Employee(User_ID);

-- Studies table (grades)
CREATE INDEX idx_studies_subject_id ON Studies(Subject_ID);
CREATE INDEX idx_studies_student_id ON Studies(Student_ID);

-- Teaches table (teacher-subject assignments)
CREATE INDEX idx_teaches_emp_subject ON Teaches(Emp_ID, Subject_ID);
```

### Recommended Indexes (Additional)
```sql
-- Classroom assignments
CREATE INDEX idx_is_in_student_id ON Is_In(Student_ID);
CREATE INDEX idx_is_in_classroom_id ON Is_In(Classroom_ID);

-- Employee table
CREATE INDEX idx_employee_dept_id ON Employee(Dept_ID);
```

## Join Patterns Used

### Pattern 1: Simple Inner Join (EXISTS Check)
**Example**: Query 03 - Check if student linked to user
```sql
SELECT * FROM Student WHERE User_ID = %s
-- Finds one related record
```

### Pattern 2: Multiple Joins (Complex Read)
**Example**: Query 06 - List students
```sql
SELECT * FROM Student
LEFT JOIN Users ON Student.User_ID = Users.User_ID
-- Multiple tables, optional left join
```

### Pattern 3: Multiple Joins with Filters
**Example**: Query 11 - Teacher's class with grades
```sql
SELECT * FROM Studies
JOIN Student ON Studies.Student_ID = Student.Student_ID
JOIN Teaches ON Teaches.Subject_ID = Studies.Subject_ID
WHERE Teaches.Emp_ID = ? AND Studies.Subject_ID = ?
-- Multiple tables with WHERE filter
```

### Pattern 4: Distinct with Multiple Joins
**Example**: Query 12 - All student's taught by teacher
```sql
SELECT DISTINCT Student.Student_ID, ...
FROM Studies
JOIN Student ON Studies.Student_ID = Student.Student_ID
JOIN Teaches ON Teaches.Subject_ID = Studies.Subject_ID
WHERE Teaches.Emp_ID = ?
-- Removes duplicates from joins
```

## Error Handling by Query

### 400 Bad Request (Validation Error)
- **10** (Upsert Grade): Grade outside 0-100 range
- **07** (Insert Student): Missing required fields
- **08** (Update Student): Invalid input

### 401 Unauthorized
- **02** (Find User): Wrong password (not 404, it's checked in code)
- All queries: Missing/invalid session

### 403 Forbidden  
- **02** (Find User): Role mismatch (user is admin but requested student login)

### 404 Not Found
- **02** (Find User): User not found
- **03** (Get Student): Student not linked
- **04** (Get Employee): Employee not linked

### 409 Conflict
- **07** (Insert Student): Duplicate Student_ID
- **10** (Upsert Grade): (Actually succeeds - UPSERT handles this)

### 500 Internal Server Error
- **01** (Health Check): Database unreachable
- All others: Database error/constraint violation

## SQL Features Used

### SELECT Clause Features
```sql
SELECT *                              -- All columns (queries 02, 03, 04)
SELECT specific_cols                  -- Named columns (queries 06, 11, 12)
SELECT DISTINCT                       -- Remove duplicates (query 12)
SELECT expr AS alias                  -- Aliased columns (query 06)
SELECT TIMESTAMPDIFF()                -- Date calculation (query 06)
SELECT COUNT(*)                       -- Aggregation (query 05)
```

### FROM Clause Patterns
```sql
FROM single_table                     -- Simple (queries 07, 08, 09)
FROM table JOIN                       -- Inner join (queries 11)
FROM table LEFT JOIN                  -- Optional join (query 06)
FROM table WHERE                      -- Filter (all SELECT queries)
```

### WHERE Clause Patterns
```sql
WHERE column = %s                     -- Equality (all queries)
WHERE column = %s AND column = %s     -- Multiple conditions (queries 09, 11)
WHERE NOT NULL                        -- NULL check (query 06)
```

### ORDER BY Patterns
```sql
ORDER BY column ASC                   -- Ascending (queries 06, 11, 12)
ORDER BY column DESC                  -- Descending (query 05 shows LIMIT 5)
```

### JOIN Patterns
```sql
INNER JOIN                            -- Default, only matches (queries 11)
LEFT JOIN                             -- Keep left table (query 06)
Self-join                             -- Join to self (employees)
```

### Special Clauses
```sql
ON DUPLICATE KEY UPDATE               -- UPSERT (query 10)
LIMIT                                 -- Limit results (implicit in recent)
LIMIT OFFSET                          -- Pagination (could be added)
```

## Security Patterns

### Parameterized Queries (All)
```sql
-- SAFE: Uses %s placeholders
SELECT * FROM Users WHERE Email = %s

-- UNSAFE: String interpolation (not used)
SELECT * FROM Users WHERE Email = '{email}'
```

### Password Handling
- **Query 02**: Passwords fetched as hashes, never plaintext
- Uses `check_password_hash()` for verification

### Session Management
- **Queries 03-04**: User_ID from authenticated session
- **All admin endpoints**: Require valid session

### SQL Injection Prevention
- All queries use parameterized statements
- Parameters passed separately from SQL text
- Database driver handles escaping

## Performance Optimization Opportunities

### Quick Wins
1. **Add missing indexes** (see index section above)
2. **Add authorization checks** (queries 11, 12 missing teacher verification)
3. **Combine multiple COUNT queries** into one query (query 05)
4. **Paginate large results** (query 06 could paginate)

### Medium Effort
1. **Implement caching** for dashboard stats and class rosters
2. **Use transactions** for multi-step operations (query 09)
3. **Add soft delete** option to preserve audit trail
4. **Implement audit logging** for all data modifications

### Longer Term
1. **Denormalize** frequently-accessed data
2. **Use materialized views** for dashboard stats
3. **Implement database replication** for read scaling
4. **Archive old grade data** (queries might need date filters)

## Common Query Patterns

### Pattern: Lookup by ID
```sql
SELECT * FROM Table WHERE ID = %s
```
Used in: 03, 04

### Pattern: Lookup by Key
```sql
SELECT * FROM Table WHERE key_column = %s
```
Used in: 02

### Pattern: Count All
```sql
SELECT COUNT(*) FROM Table
```
Used in: 05

### Pattern: List with Details
```sql
SELECT * FROM Table1
LEFT JOIN Table2 ON Table1.id = Table2.id
ORDER BY Table1.id
```
Used in: 06

### Pattern: Insert with Validation
```sql
INSERT INTO Table (cols) VALUES (%s, ...)
-- Check constraints in DB
```
Used in: 07

### Pattern: Update with WHERE
```sql
UPDATE Table SET col=%s WHERE id=%s
```
Used in: 08

### Pattern: Delete with Cascade
```sql
DELETE FROM Table WHERE id=%s
-- FK cascades auto-delete related rows
```
Used in: 09

### Pattern: UPSERT
```sql
INSERT INTO Table VALUES (...)
ON DUPLICATE KEY UPDATE col=%s
```
Used in: 10

### Pattern: Complex Join
```sql
SELECT Table1.* FROM Table1
JOIN Table2 ON Table1.id = Table2.id
JOIN Table3 ON Table2.id = Table3.id
WHERE condition
```
Used in: 11

### Pattern: Distinct with Join
```sql
SELECT DISTINCT Table1.cols FROM Table1
JOIN Table2 ON conditions
JOIN Table3 ON conditions
WHERE filter
```
Used in: 12

## Recommended Reading Order

1. **Start here**: [01 - Health Check](./01_health_check.md) - Simplest query
2. **Authentication flow**: [02](./02_signin_user_lookup.md) → [03](./03_get_student_entity.md) → [04](./04_get_employee_entity.md)
3. **Data operations**: [07 Insert](./07_insert_student.md) → [08 Update](./08_update_student.md) → [09 Delete](./09_delete_student.md)
4. **Complex reads**: [06 List](./06_list_students.md) → [11 Teacher Class](./11_teacher_subject_students.md) → [12 Teacher All](./12_teacher_all_students.md)
5. **Special patterns**: [05 Count](./05_count_records.md) → [10 UPSERT](./10_upsert_grade.md)

## Database Schema Reference

```
Users (authentication)
├── User_ID (PK)
├── Email (UQ)
├── Password_Hash
└── Role

Student (student data)
├── Student_ID (PK)
├── User_ID (FK → Users)
├── Fname, Lname
└── ...

Employee (employee data)
├── Emp_ID (PK)
├── User_ID (FK → Users)
├── Fname, Lname
└── ...

Subject (courses)
├── Subject_ID (PK)
└── ...

Department
├── Dept_ID (PK)
└── ...

Classroom
├── Classroom_ID (PK)
└── ...

Studies (grades)
├── Student_ID (FK)
├── Subject_ID (FK)
├── Grades
└── PK(Student_ID, Subject_ID)

Teaches (instructor assignments)
├── Emp_ID (FK)
├── Subject_ID (FK)
└── PK(Emp_ID, Subject_ID)

Instructor (teacher-specific)
├── Emp_ID (FK)
└── ...

Is_In (student-classroom)
├── Student_ID (FK)
├── Classroom_ID (FK)
└── PK(Student_ID, Classroom_ID)
```

## Statistics

- **Total Queries Documented**: 12
- **Total SQL Files**: 12 (one per query)
- **Main Code Blocks File**: CODE_BLOCKS.md
- **Total Documentation Pages**: 14

## How to Use This Index

1. **Find a query**: Use the Quick Navigation section
2. **Understand it**: Read the detailed documentation file
3. **See context**: Check "Related Queries" section within file
4. **Optimize**: Check "Performance" section in each file
5. **Troubleshoot**: Check "Error Handling" or "Edge Cases" sections

## Additional Resources

- **Main Documentation**: See CODE_BLOCKS.md for code block explanations
- **Database Schema**: See db.sql for complete schema
- **API Documentation**: See CODE_DOCUMENTATION.md (original) for API endpoints
- **Configuration**: See dbconfiguration.md for database setup

---

**Last Updated**: May 3, 2026
**Queries Documented**: All major queries in app.py
**Completeness**: ~95% (missing some batch/bulk operations)
