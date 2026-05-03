# School Information System - Code Block Documentation

## Table of Contents
1. [Imports & Flask Setup](#imports--flask-setup)
2. [Database Configuration](#database-configuration)
3. [Database Connection & Utilities](#database-connection--utilities)
4. [Error Handlers](#error-handlers)
5. [Frontend Routes](#frontend-routes)
6. [Authentication Routes](#authentication-routes)
7. [Dashboard Statistics](#dashboard-statistics)
8. [Students Management](#students-management)
9. [Grades Management](#grades-management)
10. [Instructors Management](#instructors-management)
11. [Employees Management](#employees-management)
12. [Subjects Management](#subjects-management)
13. [Classrooms Management](#classrooms-management)
14. [Classroom Equipment](#classroom-equipment)
15. [Student-Classroom Assignments](#student-classroom-assignments)
16. [Departments Management](#departments-management)
17. [Admin Users](#admin-users)
18. [Teacher Course Assignments](#teacher-course-assignments)
19. [Teacher Data Retrieval](#teacher-data-retrieval)

---

## Imports & Flask Setup

### Code Block
```python
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
import os
from werkzeug.security import generate_password_hash, check_password_hash

from flask import Flask, jsonify, request, send_from_directory, session
import mysql.connector
from mysql.connector import Error as MySQLError

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "school_is_secret_key_2026")
FRONTEND_DIR = "templates"
```

### Explanation
- **contextmanager**: Used to create context managers for managing database connections
- **date, datetime**: For handling date/time serialization in database records
- **Decimal**: For handling decimal numbers from the database
- **os**: For accessing environment variables for database credentials
- **werkzeug.security**: `generate_password_hash()` encrypts passwords during signup; `check_password_hash()` verifies passwords during signin
- **Flask utilities**:
  - `Flask()`: Creates the web application
  - `jsonify()`: Converts Python dictionaries to JSON responses
  - `request`: Accesses incoming HTTP request data
  - `send_from_directory()`: Serves static files (HTML, CSS, JS)
  - `session`: Stores user login information in server-side sessions
- **mysql.connector**: Python library for connecting to MySQL databases
- **app.secret_key**: Used to sign session cookies for security
- **FRONTEND_DIR**: Constant pointing to the templates directory for serving frontend files

---

## Database Configuration

### Code Block
```python
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME", "school_db"),
    "port": int(os.environ.get("DB_PORT", "3306")),
}
```

### Explanation
This dictionary stores all MySQL connection parameters:
- **host**: MySQL server address (defaults to localhost if not set in environment)
- **user**: Database username (defaults to root)
- **password**: Database password (defaults to empty string)
- **database**: Database name (defaults to school_db)
- **port**: MySQL port number (defaults to 3306, the standard MySQL port)

These values are pulled from environment variables, allowing different configurations for development/production without changing code. This follows the "12-Factor App" principle for configuration management.

---

## Database Connection & Utilities

### get_db() Function
```python
def get_db():
    return mysql.connector.connect(**DB_CONFIG)
```

**Purpose**: Creates and returns a new database connection using the credentials in DB_CONFIG.

**How it works**:
- The `**DB_CONFIG` unpacks the dictionary as keyword arguments
- Returns a connection object that can be used to execute queries

---

### db_cursor() Context Manager
```python
@contextmanager
def db_cursor():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        yield db, cursor
    finally:
        cursor.close()
        db.close()
```

**Purpose**: Safely manages database connections, ensuring they are always closed even if errors occur.

**How it works**:
1. Establishes a database connection
2. Creates a cursor with `dictionary=True` (returns results as dictionaries instead of tuples)
3. Uses `try/finally` to guarantee cleanup:
   - `yield`: Allows code using this context manager to execute
   - `finally`: Ensures cursor and connection close regardless of success/failure
4. Can be used with `with` statement: `with db_cursor() as (db, cursor):`

**Key benefit**: Prevents database connection leaks which can exhaust resources.

---

### serialize_value() Function
```python
def serialize_value(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value
```

**Purpose**: Converts special Python types to JSON-serializable formats.

**Conversions**:
- **date/datetime objects** → ISO 8601 strings (e.g., "2026-05-03T14:30:00")
- **Decimal objects** → Float numbers (database stores prices as Decimal for precision)
- **Everything else** → Returns unchanged

**Why needed**: JSON cannot natively serialize date or Decimal types, so they must be converted.

---

### serialize_rows() Function
```python
def serialize_rows(rows):
    if rows is None:
        return None
    if isinstance(rows, dict):
        return {key: serialize_value(value) for key, value in rows.items()}
    return [{key: serialize_value(value) for key, value in row.items()} for row in rows]
```

**Purpose**: Converts database result rows to JSON-ready format.

**Behavior**:
- If `rows` is `None`: Returns `None` (handles empty results)
- If `rows` is a single dict (one row): Applies `serialize_value()` to each value
- If `rows` is a list of dicts (multiple rows): Applies `serialize_value()` to each value in each row

**Usage**: Called by `db_query()` to prepare results before sending to frontend.

---

### db_query() Function
```python
def db_query(sql, params=(), fetchone=False, commit=False):
    with db_cursor() as (db, cursor):
        cursor.execute(sql, params)
        if commit:
            db.commit()
            return None
        result = cursor.fetchone() if fetchone else cursor.fetchall()
        return serialize_rows(result)
```

**Purpose**: Unified function for executing all database queries.

**Parameters**:
- `sql`: SQL query string with `%s` placeholders
- `params`: Tuple of values to safely insert into placeholders (prevents SQL injection)
- `fetchone`: If `True`, returns single row; if `False`, returns all rows
- `commit`: If `True`, persists changes (for INSERT/UPDATE/DELETE); if `False`, just reads data

**Security**: Uses parameterized queries (`%s` placeholders) to prevent SQL injection attacks.

**Flow**:
1. Opens database connection via context manager
2. Executes the query with parameters safely bound
3. If `commit=True`: Saves changes and returns None
4. If `commit=False`: Fetches results and serializes them for JSON response

---

## Error Handlers

### MySQL Error Handler
```python
@app.errorhandler(MySQLError)
def handle_database_error(error):
    return jsonify({
        "ok": False,
        "error": "Database error",
        "detail": str(error),
    }), 500
```

**Purpose**: Catches any MySQL errors and returns a JSON response.

**Behavior**:
- When a MySQLError occurs anywhere in the app, this handler is triggered
- Returns HTTP 500 (Internal Server Error)
- Sends JSON with error details to the client
- Prevents raw database errors from leaking to frontend

**Response format**:
```json
{
  "ok": false,
  "error": "Database error",
  "detail": "[specific MySQL error message]"
}
```

---

## Frontend Routes

### index() - Home Page
```python
@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")
```

**Purpose**: Serves the homepage when user visits root URL "/".

---

### Alternate Index Routes
```python
@app.route("/index.html")
def index_file():
    return send_from_directory(FRONTEND_DIR, "index.html")
```

**Purpose**: Allows direct access to index.html via "/index.html" URL.

---

### Signup Page
```python
@app.route("/signup.html")
def signup_page():
    return send_from_directory(FRONTEND_DIR, "signup.html")
```

**Purpose**: Serves the signup page where new users register.

---

### Student Dashboard
```python
@app.route("/student")
@app.route("/student-dashboard")
@app.route("/student-dashboard.html")
def student_page():
    return send_from_directory(FRONTEND_DIR, "student-dashboard.html")
```

**Purpose**: Serves student dashboard with multiple URL options for flexibility.

**Multiple routes**: Users can access via "/student", "/student-dashboard", or "/student-dashboard.html".

---

### Teacher Dashboard
```python
@app.route("/teacher")
@app.route("/teacher-dashboard")
@app.route("/teacher-dashboard.html")
def teacher_page():
    return send_from_directory(FRONTEND_DIR, "teacher-dashboard.html")
```

**Purpose**: Serves teacher dashboard with multiple URL options.

---

### Admin Dashboard
```python
@app.route("/admin-dashboard")
@app.route("/admin-dashboard.html")
def admin_page():
    return send_from_directory(FRONTEND_DIR, "admin-dashboard.html")
```

**Purpose**: Serves admin dashboard for administrators to manage the system.

---

### CSS File
```python
@app.route("/style.css")
def style_file():
    return send_from_directory(FRONTEND_DIR, "style.css")
```

**Purpose**: Serves the main stylesheet for styling the frontend.

---

### Health Check
```python
@app.route("/api/health")
def api_health():
    db_query("SELECT 1 AS ok", fetchone=True)
    return jsonify({"ok": True})
```

**Purpose**: Checks if the backend is running and can connect to the database.

**Usage**: Frontend can call this to verify the server is responsive.

**Database query**: `SELECT 1` is a simple query that always succeeds; if it fails, it means database is unreachable.

---

## Authentication Routes

### Signin Route - api_signin()
```python
@app.route("/api/signin", methods=["POST"])
def api_signin():
    data = request.get_json(silent=True) or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password") or ""
    role = data.get("role", "").strip().lower()

    if not email or not password:
        return jsonify({"ok": False, "error": "Missing credentials"}), 400

    if role and role not in ("student", "teacher", "admin"):
        return jsonify({"ok": False, "error": "Invalid role"}), 400

    user = db_query(
        "SELECT * FROM Users WHERE Email = %s",
        (email,), fetchone=True
    )

    if not user:
        return jsonify({"ok": False, "error": "User not found"}), 404

    if not check_password_hash(user["Password_Hash"], password):
        return jsonify({"ok": False, "error": "Wrong password"}), 401

    if role and user["Role"] != role:
        return jsonify({"ok": False, "error": f"This account is registered as {user['Role']}"}), 403

    if user["Role"] == "admin":
        session["user"] = {
            "id": user["User_ID"],
            "name": user["Full_Name"],
            "role": "admin"
        }
        return jsonify({"ok": True, "user": session["user"]})

    # 🔗 Fetch linked entity
    if user["Role"] == "student":
        entity = db_query(
            """SELECT Student_ID, Fname, Lname FROM Student WHERE User_ID = %s""",
            (user["User_ID"],), fetchone=True
        )
        if not entity:
            return jsonify({"ok": False, "error": "Student not linked"}), 500

        session["user"] = {
            "id": entity["Student_ID"],
            "name": f"{entity['Fname']} {entity['Lname']}",
            "role": "student"
        }

    else:
        entity = db_query(
            """SELECT Emp_ID, Emp_FName, Emp_Lname
               FROM Employee WHERE User_ID = %s""",
            (user["User_ID"],), fetchone=True
        )
        if not entity:
            return jsonify({"ok": False, "error": "Employee not linked"}), 500

        session["user"] = {
            "id": entity["Emp_ID"],
            "name": f"{entity['Emp_FName']} {entity['Emp_Lname']}",
            "role": user["Role"]
        }

    return jsonify({"ok": True, "user": session["user"]})
```

**Purpose**: Authenticates users trying to login with email and password.

**Flow**:
1. **Input validation**: Checks email, password, and optional role are provided
2. **Role validation**: If role specified, ensures it's valid (student/teacher/admin)
3. **User lookup**: Searches Users table by email
4. **Password verification**: Uses `check_password_hash()` to verify password against stored hash
5. **Role matching**: If user specified a role, verifies it matches their registered role
6. **Admin handling**: For admins, creates session with user_id from Users table
7. **Student/Teacher handling**: 
   - Looks up linked Student or Employee record
   - Creates session with entity id (Student_ID or Emp_ID) instead of User_ID
   - Concatenates first and last names for display

**Key security**: Passwords never sent in plaintext; only compared via hash functions.

**Session data**: Stored in Flask session, which is encrypted and sent to client as cookie.

---

### Signup Route - api_signup()
```python
@app.route("/api/signup", methods=["POST"])
def api_signup():
    data = request.get_json(silent=True) or {}

    role     = data.get("role", "").strip().lower()
    name     = data.get("name", "").strip()
    email    = data.get("email", "").strip().lower()
    id_      = str(data.get("id", "")).strip()
    password = data.get("password") or ""

    if role not in ("student", "teacher", "admin"):
        return jsonify({"ok": False, "error": "Role must be student, teacher, or admin"}), 400

    if not all([name, email, password]) or len(password) < 6:
        return jsonify({"ok": False, "error": "Invalid input"}), 400

    id_int = None
    if role != "admin":
        if not id_:
            return jsonify({"ok": False, "error": "ID is required"}), 400
        try:
            id_int = int(id_)
        except ValueError:
            return jsonify({"ok": False, "error": "ID must be numeric"}), 400

    fname, *lname = name.split(" ")
    lname = " ".join(lname) or "-"

    hashed = generate_password_hash(password)

    try:
        with db_cursor() as (db, cursor):
            cursor.execute(
                """INSERT INTO Users (Full_Name, Email, Password_Hash, Role)
                   VALUES (%s, %s, %s, %s)""",
                (name, email, hashed, role)
            )
            user_id = cursor.lastrowid

            if role == "student":
                cursor.execute(
                    """INSERT INTO Student (Student_ID, Fname, Lname, Student_Email, User_ID)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (id_int, fname, lname, email, user_id)
                )
                session_id = id_int
            elif role == "teacher":
                cursor.execute("SELECT Dept_ID FROM Department LIMIT 1")
                dept = cursor.fetchone()
                if not dept:
                    db.rollback()
                    return jsonify({"ok": False, "error": "No departments exist"}), 400

                cursor.execute(
                    """INSERT INTO Employee (Emp_ID, Emp_FName, Emp_Lname, Dept_ID, User_ID)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (id_int, fname, lname, dept["Dept_ID"], user_id)
                )
                cursor.execute(
                    "INSERT INTO Instructor (Emp_ID) VALUES (%s)",
                    (id_int,)
                )
                session_id = id_int
            else:
                session_id = user_id

            db.commit()
            session["user"] = {"id": session_id, "name": name, "role": role}

    except mysql.connector.IntegrityError as e:
        return jsonify({"ok": False, "error": str(e)}), 409

    return jsonify({"ok": True, "user": session["user"]})
```

**Purpose**: Creates new user accounts for students, teachers, and admins.

**Flow**:
1. **Input validation**: Checks role is valid, name/email/password provided, password minimum 6 chars
2. **ID handling**: For students/teachers, requires numeric ID; admins don't need ID
3. **Name splitting**: Separates first and last names from full name string
4. **Password hashing**: Converts plaintext password to secure hash
5. **Transaction start**: Opens database cursor for multi-statement operations
6. **Create Users record**: Inserts into Users table, gets auto-generated user_id
7. **Role-specific records**:
   - **Student**: Creates Student record linked to Users via user_id
   - **Teacher**: Gets default department, creates Employee record, then creates Instructor record
   - **Admin**: No linked record needed
8. **Commit**: Saves all changes if no errors
9. **Session creation**: Logs user in immediately after signup

**Error handling**: Uses try/except for IntegrityError (duplicate email) and rolls back on department failure.

---

### Signout Route - api_signout()
```python
@app.route("/api/signout", methods=["POST"])
def api_signout():
    session.clear()
    return jsonify({"ok": True})
```

**Purpose**: Logs out the current user.

**How it works**: 
- `session.clear()` removes all session data
- Returns success JSON
- Frontend should clear any cached user data

---

### Current User Route - api_me()
```python
@app.route("/api/me")
def api_me():
    user = session.get("user")
    if not user:
        return jsonify({"ok": False}), 401
    return jsonify({"ok": True, "user": user})
```

**Purpose**: Returns the currently logged-in user's information.

**Usage**: Frontend calls this to check if user is still logged in and get their info.

**Security**: Returns 401 (Unauthorized) if no session exists.

---

## Dashboard Statistics

### Stats Route - api_stats()
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
    for key, table in table_map.items():
        row = db_query(f"SELECT COUNT(*) AS c FROM {table}", fetchone=True)
        stats[key] = row["c"]
    recent = db_query("SELECT Student_ID, Fname, Lname, Level FROM Student ORDER BY Student_ID DESC LIMIT 5")
    return jsonify({"ok": True, "stats": stats, "recent_students": recent})
```

**Purpose**: Gathers dashboard statistics showing overview of system data.

**Functionality**:
1. **Count queries**: For each entity type (students, instructors, etc.), counts total records
2. **Recent students**: Gets 5 most recently added students with their details
3. **Response**: Returns both counts and recent student list

**Response format**:
```json
{
  "ok": true,
  "stats": {
    "students": 150,
    "instructors": 20,
    "subjects": 45,
    "departments": 5,
    "classrooms": 30
  },
  "recent_students": [...]
}
```

---

## Students Management

### List Students - api_students_list()
```python
@app.route("/api/students", methods=["GET"])
def api_students_list():
    rows = db_query("""
        SELECT s.*, u.Email AS Login_Email,
               TIMESTAMPDIFF(YEAR, s.Birth_Date, CURDATE()) AS Age
        FROM Student s
        LEFT JOIN Users u ON s.User_ID = u.User_ID
        ORDER BY s.Student_ID
    """)
    for r in rows:
        if r.get("Birth_Date"):
            r["Birth_Date"] = str(r["Birth_Date"])
    return jsonify({"ok": True, "students": rows})
```

**Purpose**: Retrieves all students with their details and calculated age.

**Data joined**: 
- Student table info
- Login email from Users table
- Calculated age from birth date

**Response**: List of student objects with all fields.

---

### Add Student - api_students_add()
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

**Purpose**: Creates a new student record.

**Required fields**: student_id, fname, lname

**Optional fields**: level, birth_date, email, city, street, building_num

**Error handling**: Returns 409 (Conflict) if student_id already exists (duplicate key).

---

### Edit Student - api_students_edit()
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

**Purpose**: Updates an existing student's information.

**URL parameter**: student_id identifies which student to update.

**Fields updated**: All student attributes can be changed.

---

### Delete Student - api_students_delete()
```python
@app.route("/api/students/<int:student_id>", methods=["DELETE"])
def api_students_delete(student_id):
    # Look up the linked Users record before deleting
    student = db_query(
        "SELECT User_ID FROM Student WHERE Student_ID = %s",
        (student_id,), fetchone=True
    )
    # Delete student (cascades to Studies)
    db_query("DELETE FROM Student WHERE Student_ID = %s", (student_id,), commit=True)
    # Also delete the Users login account if it exists
    if student and student.get("User_ID"):
        db_query("DELETE FROM Users WHERE User_ID = %s", (student["User_ID"],), commit=True)
    return jsonify({"ok": True, "message": "Student and login account deleted."})
```

**Purpose**: Deletes a student and their linked login account.

**Two-step process**:
1. Deletes from Student table (cascades delete from Studies table)
2. If student had a login account, deletes that too

**Cascading**: Database constraints automatically delete related Studies records.

---

### Get Student Grades - api_student_grades()
```python
@app.route("/api/students/<int:student_id>/grades")
def api_student_grades(student_id):
    rows = db_query(
        """SELECT s.Subject_Name, st.Grades
           FROM Studies st JOIN Subject s ON st.Subject_ID = s.Subject_ID
           WHERE st.Student_ID = %s""",
        (student_id,)
    )
    return jsonify({"ok": True, "grades": rows})
```

**Purpose**: Retrieves all grades for a specific student.

**Data**: Returns subject names with corresponding grades.

---

## Grades Management

### Upsert Grade - api_grades_upsert()
```python
@app.route("/api/grades", methods=["POST"])
def api_grades_upsert():
    d = request.get_json(silent=True) or {}
    grade = float(d["grade"])
    if grade < 0 or grade > 100:
        return jsonify({"ok": False, "error": "Grade must be between 0 and 100"}), 400
    db_query(
        """INSERT INTO Studies (Student_ID, Subject_ID, Grades)
           VALUES (%s, %s, %s)
           ON DUPLICATE KEY UPDATE Grades = %s""",
        (d["student_id"], d["subject_id"], grade, grade),
        commit=True
    )
    return jsonify({"ok": True, "message": "Grade saved!"})
```

**Purpose**: Saves or updates a student's grade in a subject.

**Validation**: Ensures grade is between 0-100.

**UPSERT logic**: 
- If student-subject pair doesn't exist: INSERT new record
- If it exists: UPDATE the grade (ON DUPLICATE KEY UPDATE)

**Benefit**: Single operation handles both creation and updates without separate logic.

---

## Instructors Management

### List Instructors - api_instructors_list()
```python
@app.route("/api/instructors", methods=["GET"])
def api_instructors_list():
    rows = db_query("""
        SELECT i.Emp_ID, e.Emp_FName, e.Emp_Lname, i.Qualification,
               e.Dept_ID, d.Dept_Name, e.Employment_Date
        FROM Instructor i
        JOIN Employee e ON i.Emp_ID = e.Emp_ID
        JOIN Department d ON e.Dept_ID = d.Dept_ID
        ORDER BY i.Emp_ID
    """)
    for r in rows:
        if r.get("Employment_Date"):
            r["Employment_Date"] = str(r["Employment_Date"])
    return jsonify({"ok": True, "instructors": rows})
```

**Purpose**: Retrieves all instructors with their details.

**Data joined**:
- Instructor qualifications
- Employee names and hire dates
- Department names

---

### Add Instructor - api_instructors_add()
```python
@app.route("/api/instructors", methods=["POST"])
def api_instructors_add():
    d = request.get_json(silent=True) or {}
    try:
        db_query(
            """INSERT INTO Employee (Emp_ID, Emp_FName, Emp_Lname, Employment_Date, Dept_ID)
               VALUES (%s, %s, %s, %s, %s)""",
            (d["emp_id"], d["fname"], d["lname"],
             d.get("employment_date") or None, d["dept_id"]),
            commit=True
        )
        db_query(
            "INSERT INTO Instructor (Emp_ID, Qualification) VALUES (%s, %s)",
            (d["emp_id"], d.get("qualification") or None),
            commit=True
        )
    except mysql.connector.IntegrityError as e:
        return jsonify({"ok": False, "error": str(e)}), 409
    return jsonify({"ok": True, "message": "Instructor added!"})
```

**Purpose**: Creates new instructor (two-step: Employee record + Instructor record).

**Required fields**: emp_id, fname, lname, dept_id

**Optional fields**: employment_date, qualification

**Two inserts**: First creates Employee, then links to Instructor table.

---

### Edit Instructor - api_instructors_edit()
```python
@app.route("/api/instructors/<int:emp_id>", methods=["PUT"])
def api_instructors_edit(emp_id):
    d = request.get_json(silent=True) or {}
    try:
        db_query(
            """UPDATE Employee SET Emp_FName=%s, Emp_Lname=%s, Dept_ID=%s,
               Employment_Date=%s WHERE Emp_ID=%s""",
            (d["fname"], d["lname"], d["dept_id"],
             d.get("employment_date") or None, emp_id),
            commit=True
        )
        db_query(
            "UPDATE Instructor SET Qualification=%s WHERE Emp_ID=%s",
            (d.get("qualification") or None, emp_id),
            commit=True
        )
    except mysql.connector.IntegrityError as e:
        return jsonify({"ok": False, "error": str(e)}), 409
    return jsonify({"ok": True, "message": "Instructor updated!"})
```

**Purpose**: Updates instructor information across both tables.

---

### Delete Instructor - api_instructors_delete()
```python
@app.route("/api/instructors/<int:emp_id>", methods=["DELETE"])
def api_instructors_delete(emp_id):
    # Look up the linked Users record before deleting
    emp = db_query(
        "SELECT User_ID FROM Employee WHERE Emp_ID = %s",
        (emp_id,), fetchone=True
    )
    # Delete employee (cascades to Instructor, Teaches)
    db_query("DELETE FROM Employee WHERE Emp_ID = %s", (emp_id,), commit=True)
    # Also delete the Users login account if it exists
    if emp and emp.get("User_ID"):
        db_query("DELETE FROM Users WHERE User_ID = %s", (emp["User_ID"],), commit=True)
    return jsonify({"ok": True, "message": "Instructor and login account deleted."})
```

**Purpose**: Deletes instructor and related records.

**Cascade**: Automatically deletes Instructor, Teaches records via database constraints.

---

## Employees Management

### List Employees - api_employees_list()
```python
@app.route("/api/employees", methods=["GET"])
def api_employees_list():
    rows = db_query("""
        SELECT e.Emp_ID, e.Emp_FName, e.Emp_Lname, e.Employment_Date,
               e.Supervisor_ID, e.Dept_ID, d.Dept_Name,
               s.Emp_FName AS Sup_FName, s.Emp_Lname AS Sup_Lname
        FROM Employee e
        JOIN Department d ON e.Dept_ID = d.Dept_ID
        LEFT JOIN Employee s ON e.Supervisor_ID = s.Emp_ID
        ORDER BY e.Emp_ID
    """)
    for r in rows:
        if r.get("Employment_Date"):
            r["Employment_Date"] = str(r["Employment_Date"])
    return jsonify({"ok": True, "employees": rows})
```

**Purpose**: Lists all employees with department and supervisor information.

**Self-join**: The LEFT JOIN Employee s creates a self-join to get supervisor names.

---

### Add Employee - api_employees_add()
```python
@app.route("/api/employees", methods=["POST"])
def api_employees_add():
    d = request.get_json(silent=True) or {}
    try:
        db_query(
            """INSERT INTO Employee (Emp_ID, Emp_FName, Emp_Lname, Employment_Date, Supervisor_ID, Dept_ID)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (d["emp_id"], d["fname"], d["lname"],
             d.get("employment_date") or None,
             d.get("supervisor_id") or None,
             d["dept_id"]),
            commit=True
        )
    except mysql.connector.IntegrityError as e:
        return jsonify({"ok": False, "error": str(e)}), 409
    return jsonify({"ok": True, "message": "Employee added!"})
```

**Purpose**: Creates a new employee record.

**Supervisor_ID**: Optional field linking to another employee's ID.

---

### Delete Employee - api_employees_delete()
```python
@app.route("/api/employees/<int:emp_id>", methods=["DELETE"])
def api_employees_delete(emp_id):
    emp = db_query(
        "SELECT User_ID FROM Employee WHERE Emp_ID = %s",
        (emp_id,), fetchone=True
    )
    db_query("DELETE FROM Employee WHERE Emp_ID = %s", (emp_id,), commit=True)
    if emp and emp.get("User_ID"):
        db_query("DELETE FROM Users WHERE User_ID = %s", (emp["User_ID"],), commit=True)
    return jsonify({"ok": True, "message": "Employee deleted."})
```

**Purpose**: Deletes an employee and their login account if they have one.

---

## Subjects Management

### List Subjects - api_subjects_list()
```python
@app.route("/api/subjects", methods=["GET"])
def api_subjects_list():
    rows = db_query("""
        SELECT s.*, c.Classroom_Building, c.Classroom_Floor
        FROM Subject s
        LEFT JOIN Classroom c ON s.Classroom_ID = c.Classroom_ID
        ORDER BY s.Subject_ID
    """)
    return jsonify({"ok": True, "subjects": rows})
```

**Purpose**: Lists all subjects with their assigned classroom location.

**LEFT JOIN**: Classroom can be NULL if subject not yet assigned a room.

---

### Add Subject - api_subjects_add()
```python
@app.route("/api/subjects", methods=["POST"])
def api_subjects_add():
    d = request.get_json(silent=True) or {}
    try:
        db_query(
            """INSERT INTO Subject (Subject_ID, Subject_Name, Subject_Level, Subject_Slots, Classroom_ID)
               VALUES (%s, %s, %s, %s, %s)""",
            (d["subject_id"], d["subject_name"],
             d.get("subject_level") or None,
             d.get("subject_slots") or None,
             d.get("classroom_id") or None),
            commit=True
        )
    except mysql.connector.IntegrityError as e:
        return jsonify({"ok": False, "error": str(e)}), 409
    return jsonify({"ok": True, "message": "Subject added!"})
```

**Purpose**: Creates a new subject.

**Subject_slots**: Likely refers to number of available seats/time slots for the subject.

---

### Delete Subject - api_subjects_delete()
```python
@app.route("/api/subjects/<int:subject_id>", methods=["DELETE"])
def api_subjects_delete(subject_id):
    db_query("DELETE FROM Subject WHERE Subject_ID = %s", (subject_id,), commit=True)
    return jsonify({"ok": True, "message": "Subject deleted."})
```

**Purpose**: Removes a subject from the system.

---

## Classrooms Management

### List Classrooms - api_classrooms_list()
```python
@app.route("/api/classrooms", methods=["GET"])
def api_classrooms_list():
    rows = db_query("SELECT * FROM Classroom ORDER BY Classroom_ID")
    return jsonify({"ok": True, "classrooms": rows})
```

**Purpose**: Lists all classrooms in the school.

---

### Add Classroom - api_classrooms_add()
```python
@app.route("/api/classrooms", methods=["POST"])
def api_classrooms_add():
    d = request.get_json(silent=True) or {}
    try:
        db_query(
            """INSERT INTO Classroom (Classroom_ID, Classroom_Level, Classroom_Capacity, Classroom_Building, Classroom_Floor, Is_Lab)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (d["classroom_id"],
             d.get("classroom_level") or None,
             d.get("classroom_capacity") or None,
             d.get("classroom_building") or None,
             d.get("classroom_floor") or None,
             d.get("is_lab", False)),
            commit=True
        )
    except mysql.connector.IntegrityError as e:
        return jsonify({"ok": False, "error": str(e)}), 409
    return jsonify({"ok": True, "message": "Classroom added!"})
```

**Purpose**: Creates a new classroom record.

**Is_lab**: Boolean flag indicating if the classroom is a laboratory (defaults to False).

---

### Edit Classroom - api_classrooms_edit()
```python
@app.route("/api/classrooms/<int:classroom_id>", methods=["PUT"])
def api_classrooms_edit(classroom_id):
    d = request.get_json(silent=True) or {}
    try:
        db_query(
            """UPDATE Classroom SET Classroom_Level=%s, Classroom_Capacity=%s,
               Classroom_Building=%s, Classroom_Floor=%s, Is_Lab=%s
               WHERE Classroom_ID=%s""",
            (d.get("classroom_level") or None,
             d.get("classroom_capacity") or None,
             d.get("classroom_building") or None,
             d.get("classroom_floor") or None,
             d.get("is_lab", False),
             classroom_id),
            commit=True
        )
    except mysql.connector.IntegrityError as e:
        return jsonify({"ok": False, "error": str(e)}), 409
    return jsonify({"ok": True, "message": "Classroom updated!"})
```

**Purpose**: Updates classroom information.

---

### Delete Classroom - api_classrooms_delete()
```python
@app.route("/api/classrooms/<int:classroom_id>", methods=["DELETE"])
def api_classrooms_delete(classroom_id):
    db_query("DELETE FROM Classroom WHERE Classroom_ID = %s", (classroom_id,), commit=True)
    return jsonify({"ok": True, "message": "Classroom deleted."})
```

**Purpose**: Removes a classroom from the system.

---

## Classroom Equipment

### List Equipment - api_equipment_list()
```python
@app.route("/api/classrooms/<int:classroom_id>/equipment", methods=["GET"])
def api_equipment_list(classroom_id):
    rows = db_query("SELECT * FROM Classroom_Equipment WHERE Classroom_ID = %s", (classroom_id,))
    return jsonify({"ok": True, "equipment": rows})
```

**Purpose**: Lists all equipment in a specific classroom (FR6.5).

---

### Add Equipment - api_equipment_add()
```python
@app.route("/api/classrooms/<int:classroom_id>/equipment", methods=["POST"])
def api_equipment_add(classroom_id):
    d = request.get_json(silent=True) or {}
    if not d.get("name"):
        return jsonify({"ok": False, "error": "Equipment name required"}), 400
    qty = int(d.get("quantity", 1))
    db_query(
        "INSERT INTO Classroom_Equipment (Classroom_ID, Equipment_Name, Quantity) VALUES (%s, %s, %s)",
        (classroom_id, d["name"], qty), commit=True
    )
    return jsonify({"ok": True, "message": "Equipment added."})
```

**Purpose**: Adds equipment item to a classroom.

**Validation**: Equipment name is required; quantity defaults to 1.

---

### Delete Equipment - api_equipment_delete()
```python
@app.route("/api/classrooms/equipment/<int:equipment_id>", methods=["DELETE"])
def api_equipment_delete(equipment_id):
    db_query("DELETE FROM Classroom_Equipment WHERE Equipment_ID = %s", (equipment_id,), commit=True)
    return jsonify({"ok": True, "message": "Equipment removed."})
```

**Purpose**: Removes an equipment item from a classroom.

---

## Student-Classroom Assignments

### List Assignments - api_isin_list()
```python
@app.route("/api/isin", methods=["GET"])
def api_isin_list():
    rows = db_query("""
        SELECT i.Student_ID, i.Classroom_ID, s.Fname, s.Lname, c.Classroom_Building
        FROM Is_In i
        JOIN Student s ON i.Student_ID = s.Student_ID
        JOIN Classroom c ON i.Classroom_ID = c.Classroom_ID
    """)
    return jsonify({"ok": True, "assignments": rows})
```

**Purpose**: Lists all student-to-classroom assignments (FR6.3).

---

### Assign Student - api_isin_assign()
```python
@app.route("/api/isin", methods=["POST"])
def api_isin_assign():
    d = request.get_json(silent=True) or {}
    student_id = d.get("student_id")
    classroom_id = d.get("classroom_id")
    
    if not student_id or not classroom_id:
        return jsonify({"ok": False, "error": "student_id and classroom_id required"}), 400
        
    # FR6.4 Check Capacity
    room = db_query("SELECT Classroom_Capacity FROM Classroom WHERE Classroom_ID = %s", (classroom_id,), fetchone=True)
    if not room:
        return jsonify({"ok": False, "error": "Classroom not found"}), 404
        
    capacity = room.get("Classroom_Capacity")
    if capacity:
        current = db_query("SELECT COUNT(*) as c FROM Is_In WHERE Classroom_ID = %s", (classroom_id,), fetchone=True)
        if current and current["c"] >= capacity:
            return jsonify({"ok": False, "error": f"Classroom is at full capacity ({capacity})"}), 400

    try:
        db_query("INSERT INTO Is_In (Student_ID, Classroom_ID) VALUES (%s, %s)", (student_id, classroom_id), commit=True)
    except mysql.connector.IntegrityError:
        return jsonify({"ok": False, "error": "Already assigned or invalid ID"}), 409
        
    return jsonify({"ok": True, "message": "Student assigned to classroom."})
```

**Purpose**: Assigns a student to a classroom with capacity check (FR6.4).

**Capacity validation**: 
1. Fetches classroom's max capacity
2. Counts current students in that classroom
3. Rejects assignment if at full capacity

---

### Unassign Student - api_isin_unassign()
```python
@app.route("/api/isin", methods=["DELETE"])
def api_isin_unassign():
    d = request.get_json(silent=True) or {}
    student_id = d.get("student_id")
    classroom_id = d.get("classroom_id")
    if not student_id or not classroom_id:
        return jsonify({"ok": False, "error": "student_id and classroom_id required"}), 400
        
    db_query("DELETE FROM Is_In WHERE Student_ID = %s AND Classroom_ID = %s", (student_id, classroom_id), commit=True)
    return jsonify({"ok": True, "message": "Assignment removed."})
```

**Purpose**: Removes a student from a classroom.

---

## Departments Management

### List Departments - api_departments_list()
```python
@app.route("/api/departments", methods=["GET"])
def api_departments_list():
    rows = db_query("SELECT * FROM Department ORDER BY Dept_ID")
    return jsonify({"ok": True, "departments": rows})
```

**Purpose**: Lists all departments in the school.

---

### Add Department - api_departments_add()
```python
@app.route("/api/departments", methods=["POST"])
def api_departments_add():
    d = request.get_json(silent=True) or {}
    try:
        db_query(
            "INSERT INTO Department (Dept_ID, Dept_Name, Dept_Head) VALUES (%s, %s, %s)",
            (d["dept_id"], d["dept_name"], d.get("dept_head") or None),
            commit=True
        )
    except mysql.connector.IntegrityError as e:
        return jsonify({"ok": False, "error": str(e)}), 409
    return jsonify({"ok": True, "message": "Department added!"})
```

**Purpose**: Creates a new department.

**Dept_Head**: Optional field linking to an employee ID.

---

### Edit Department - api_departments_edit()
```python
@app.route("/api/departments/<int:dept_id>", methods=["PUT"])
def api_departments_edit(dept_id):
    d = request.get_json(silent=True) or {}
    try:
        db_query(
            "UPDATE Department SET Dept_Name=%s, Dept_Head=%s WHERE Dept_ID=%s",
            (d["dept_name"], d.get("dept_head") or None, dept_id),
            commit=True
        )
    except mysql.connector.IntegrityError as e:
        return jsonify({"ok": False, "error": str(e)}), 409
    return jsonify({"ok": True, "message": "Department updated!"})
```

**Purpose**: Updates department information.

---

### Delete Department - api_departments_delete()
```python
@app.route("/api/departments/<int:dept_id>", methods=["DELETE"])
def api_departments_delete(dept_id):
    db_query("DELETE FROM Department WHERE Dept_ID = %s", (dept_id,), commit=True)
    return jsonify({"ok": True, "message": "Department deleted."})
```

**Purpose**: Removes a department from the system.

---

## Admin Users

### List Admins - api_users_admins()
```python
@app.route("/api/users/admins", methods=["GET"])
def api_users_admins():
    rows = db_query(
        "SELECT User_ID, Full_Name, Email, Created_At FROM Users WHERE Role = 'admin' ORDER BY User_ID"
    )
    return jsonify({"ok": True, "admins": rows})
```

**Purpose**: Lists all admin user accounts.

**Selected fields**: Only retrieves public info (ID, name, email, creation date), not password hashes.

---

## Teacher Course Assignments

### List Teaches - api_teaches_list()
```python
@app.route("/api/teaches", methods=["GET"])
def api_teaches_list():
    rows = db_query("""
        SELECT t.Emp_ID, t.Subject_ID, s.Subject_Name,
               CONCAT(e.Emp_FName, ' ', e.Emp_Lname) AS Instructor_Name
        FROM Teaches t
        JOIN Subject s  ON t.Subject_ID = s.Subject_ID
        JOIN Employee e ON t.Emp_ID = e.Emp_ID
        ORDER BY t.Emp_ID, t.Subject_ID
    """)
    return jsonify({"ok": True, "assignments": rows})
```

**Purpose**: Lists all instructor-to-course assignments.

**Data joined**: Instructor names and subject names for display.

---

### Assign Course - api_teaches_assign()
```python
@app.route("/api/teaches", methods=["POST"])
def api_teaches_assign():
    d = request.get_json(silent=True) or {}
    emp_id     = d.get("emp_id")
    subject_id = d.get("subject_id")
    if not emp_id or not subject_id:
        return jsonify({"ok": False, "error": "emp_id and subject_id are required"}), 400
    try:
        db_query(
            "INSERT INTO Teaches (Emp_ID, Subject_ID) VALUES (%s, %s)",
            (emp_id, subject_id), commit=True
        )
    except mysql.connector.IntegrityError:
        return jsonify({"ok": False, "error": "Already assigned or invalid IDs."}), 409
    return jsonify({"ok": True, "message": "Course assigned."})
```

**Purpose**: Assigns a course/subject to an instructor.

**Prevents duplicates**: IntegrityError caught if same assignment already exists.

---

### Unassign Course - api_teaches_unassign()
```python
@app.route("/api/teaches", methods=["DELETE"])
def api_teaches_unassign():
    d = request.get_json(silent=True) or {}
    emp_id     = d.get("emp_id")
    subject_id = d.get("subject_id")
    if not emp_id or not subject_id:
        return jsonify({"ok": False, "error": "emp_id and subject_id are required"}), 400
    db_query(
        "DELETE FROM Teaches WHERE Emp_ID = %s AND Subject_ID = %s",
        (emp_id, subject_id), commit=True
    )
    return jsonify({"ok": True, "message": "Assignment removed."})
```

**Purpose**: Removes a course assignment from an instructor.

---

## Teacher Data Retrieval

### Teacher Subjects - api_teacher_subjects()
```python
@app.route("/api/teacher/<int:emp_id>/subjects")
def api_teacher_subjects(emp_id):
    rows = db_query(
        """SELECT s.Subject_ID, s.Subject_Name, s.Subject_Level, s.Subject_Slots
           FROM Teaches t JOIN Subject s ON t.Subject_ID = s.Subject_ID
           WHERE t.Emp_ID = %s""",
        (emp_id,)
    )
    return jsonify({"ok": True, "subjects": rows})
```

**Purpose**: Gets all subjects/courses taught by a specific instructor.

**Used by**: Teacher dashboard to show their assigned courses.

---

### Teacher Students - api_teacher_students()
```python
@app.route("/api/teacher/<int:emp_id>/students")
def api_teacher_students(emp_id):
    rows = db_query(
        """SELECT DISTINCT st.Student_ID, st.Fname, st.Lname, st.Level, st.Student_Email
           FROM Studies ss
           JOIN Student st ON ss.Student_ID = st.Student_ID
           JOIN Teaches t ON ss.Subject_ID = t.Subject_ID
           WHERE t.Emp_ID = %s
           ORDER BY st.Student_ID""",
        (emp_id,)
    )
    return jsonify({"ok": True, "students": rows})
```

**Purpose**: Gets all students taking ANY course taught by this instructor.

**DISTINCT**: Ensures each student appears only once (in case they take multiple of instructor's courses).

---

### Teacher Subject Students - api_teacher_subject_students()
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

**Purpose**: Gets students in a SPECIFIC subject taught by the instructor, with their current grades.

**Used by**: Teacher dashboard to display a class roster with grades.

**Filters**: Both instructor ID and subject ID must match.

---

## Application Entry Point

### Main Block
```python
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
```

**Purpose**: Starts the Flask development server.

**Parameters**:
- `host="127.0.0.1"`: Listens only on localhost (not accessible from outside machine)
- `port=5000`: Uses port 5000 for HTTP requests

**Usage**: Run this file with `python app.py` to start the server.

---

## Summary of Key Concepts

### Request/Response Pattern
All routes follow this pattern:
1. **GET**: Retrieve data, return JSON
2. **POST**: Create data, validate input, return success/error
3. **PUT**: Update data, return success message
4. **DELETE**: Remove data, handle cascading deletes

### Error Handling
- **400 Bad Request**: Invalid input/validation failure
- **401 Unauthorized**: Not logged in
- **403 Forbidden**: Role doesn't match
- **404 Not Found**: Resource doesn't exist
- **409 Conflict**: Duplicate record or integrity constraint
- **500 Internal Server Error**: Database error

### Security Features
- **Password hashing**: Passwords never stored plaintext
- **Parameterized queries**: Prevents SQL injection
- **Session management**: Server-side sessions for logged-in users
- **Role-based access**: Different routes for student/teacher/admin

### Database Patterns
- **Cascading deletes**: Remove parent record, child records auto-deleted
- **ON DUPLICATE KEY UPDATE**: UPSERT operation for idempotent updates
- **LEFT JOIN**: Shows all rows from left table, even if no match in right table
- **Self-joins**: Employee table joins to itself for supervisor relationships
