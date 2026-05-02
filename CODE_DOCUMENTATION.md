# School Information System - Complete Code Documentation

This document explains every block of code in the School Information System workspace.

---

## Table of Contents
1. [Database Schema (db.sql)](#database-schema)
2. [Backend Application (app.py)](#backend-application)
3. [Frontend Templates](#frontend-templates)
4. [Styling (style.css)](#styling)
5. [Dependencies (requirements.txt)](#dependencies)

---

## Database Schema

### File: `db.sql`

The database schema defines the structure for a school management system with 9 main tables and their relationships.

#### Database Initialization
```sql
DROP DATABASE IF EXISTS school_db;
CREATE DATABASE school_db;
USE school_db;
```
- **Drops** the existing database to ensure a clean start
- **Creates** a new database called `school_db`
- **Uses** the new database for all subsequent operations

#### Users Table
```sql
CREATE TABLE Users (
    User_ID INT AUTO_INCREMENT PRIMARY KEY,
    Full_Name VARCHAR(100) NOT NULL,
    Email VARCHAR(150) NOT NULL UNIQUE,
    Password_Hash VARCHAR(255) NOT NULL,
    Role ENUM('student', 'teacher', 'admin') NOT NULL,
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
- **User_ID**: Auto-incrementing primary key for each user
- **Full_Name**: User's complete name (required)
- **Email**: User's email (unique constraint prevents duplicates, required)
- **Password_Hash**: Hashed password using Werkzeug security (required)
- **Role**: Enum restricting users to three types: student, teacher, or admin
- **Created_At**: Automatically records creation timestamp

#### Department Table
```sql
CREATE TABLE Department (
    Dept_ID INT PRIMARY KEY,
    Dept_Name VARCHAR(100) NOT NULL,
    Dept_Head VARCHAR(100)
);

INSERT INTO Department (Dept_ID, Dept_Name, Dept_Head)
VALUES (1, 'General Studies', 'System Administrator');
```
- **Dept_ID**: Primary key (manually specified)
- **Dept_Name**: Department name (required)
- **Dept_Head**: Name of department head (optional)
- **Inserted default**: One default department "General Studies" for new instructors

#### Student Table
```sql
CREATE TABLE Student (
    Student_ID INT PRIMARY KEY,
    User_ID INT UNIQUE,
    Fname VARCHAR(50) NOT NULL,
    Lname VARCHAR(50) NOT NULL,
    Level VARCHAR(50),
    Birth_Date DATE,
    Student_Email VARCHAR(150),
    City VARCHAR(100),
    Street VARCHAR(150),
    Building_Num VARCHAR(20),
    FOREIGN KEY (User_ID) REFERENCES Users(User_ID) ON DELETE CASCADE
);
```
- **Student_ID**: Primary key (manually assigned)
- **User_ID**: Foreign key linking to Users table (unique, cascade delete)
- **Fname, Lname**: First and last names (required)
- **Level**: Academic level (e.g., "Freshman", "Year 2") (optional)
- **Birth_Date**: Date of birth (optional)
- **Student_Email**: Student's email address (optional)
- **Address fields**: City, Street, Building_Num for composite address attribute (optional)

#### Employee Table
```sql
CREATE TABLE Employee (
    Emp_ID INT PRIMARY KEY,
    User_ID INT UNIQUE,
    Emp_FName VARCHAR(50) NOT NULL,
    Emp_Lname VARCHAR(50) NOT NULL,
    Employment_Date DATE,
    Supervisor_ID INT,
    Dept_ID INT NOT NULL,
    FOREIGN KEY (User_ID) REFERENCES Users(User_ID) ON DELETE CASCADE,
    FOREIGN KEY (Supervisor_ID) REFERENCES Employee(Emp_ID),
    FOREIGN KEY (Dept_ID) REFERENCES Department(Dept_ID)
);
```
- **Emp_ID**: Primary key (manually assigned)
- **User_ID**: Foreign key to Users (cascade delete)
- **Emp_FName, Emp_Lname**: Employee names (required)
- **Employment_Date**: Date hired (optional)
- **Supervisor_ID**: Self-referencing foreign key for supervisory hierarchy (optional)
- **Dept_ID**: Foreign key to Department (required)

#### Employee_Phone Table (Multivalued Attribute)
```sql
CREATE TABLE Employee_Phone (
    Emp_ID INT NOT NULL,
    Emp_pnum VARCHAR(20) NOT NULL,
    PRIMARY KEY (Emp_ID, Emp_pnum),
    FOREIGN KEY (Emp_ID) REFERENCES Employee(Emp_ID) ON DELETE CASCADE
);
```
- **Composite primary key**: (Emp_ID, Emp_pnum) allows one employee to have multiple phone numbers
- Handles the multivalued attribute of employee phone numbers
- Cascade delete ensures phones are deleted when employee is deleted

#### Instructor Table (Specialization of Employee)
```sql
CREATE TABLE Instructor (
    Emp_ID INT PRIMARY KEY,
    Qualification VARCHAR(200),
    FOREIGN KEY (Emp_ID) REFERENCES Employee(Emp_ID) ON DELETE CASCADE
);
```
- **Emp_ID**: Primary key AND foreign key to Employee (cascade delete)
- **Qualification**: Teaching qualifications (e.g., "PhD Computer Science") (optional)
- Represents specialization: teachers are employees with additional qualification info

#### Classroom Table
```sql
CREATE TABLE Classroom (
    Classroom_ID INT PRIMARY KEY,
    Classroom_Level VARCHAR(50),
    Classroom_Capacity INT,
    Classroom_Building VARCHAR(100),
    Classroom_Floor VARCHAR(20)
);
```
- **Classroom_ID**: Primary key (manually assigned)
- **Classroom_Level**: Level taught in classroom (e.g., "Advanced") (optional)
- **Classroom_Capacity**: Number of students capacity (optional)
- **Classroom_Building**: Building location name (optional)
- **Classroom_Floor**: Floor number (optional)

#### Subject Table
```sql
CREATE TABLE Subject (
    Subject_ID INT PRIMARY KEY,
    Subject_Name VARCHAR(100) NOT NULL,
    Subject_Level VARCHAR(50),
    Subject_Slots INT,
    Classroom_ID INT,
    FOREIGN KEY (Classroom_ID) REFERENCES Classroom(Classroom_ID)
);
```
- **Subject_ID**: Primary key (manually assigned)
- **Subject_Name**: Course name (required)
- **Subject_Level**: Level of course (optional)
- **Subject_Slots**: Number of available student slots (optional)
- **Classroom_ID**: Which classroom it's held in (foreign key, optional)

#### Studies Table (Student ↔ Subject Relationship)
```sql
CREATE TABLE Studies (
    Student_ID INT NOT NULL,
    Subject_ID INT NOT NULL,
    Grades DECIMAL(5,2),
    PRIMARY KEY (Student_ID, Subject_ID),
    FOREIGN KEY (Student_ID) REFERENCES Student(Student_ID) ON DELETE CASCADE,
    FOREIGN KEY (Subject_ID) REFERENCES Subject(Subject_ID) ON DELETE CASCADE
);
```
- **Composite primary key**: (Student_ID, Subject_ID) ensures one enrollment per student per subject
- **Grades**: Student's grade in that subject (optional, 5 digits with 2 decimals)
- Cascade delete removes enrollments if student or subject is deleted
- Represents many-to-many relationship between Students and Subjects

#### Teaches Table (Instructor ↔ Subject Relationship)
```sql
CREATE TABLE Teaches (
    Emp_ID INT NOT NULL,
    Subject_ID INT NOT NULL,
    PRIMARY KEY (Emp_ID, Subject_ID),
    FOREIGN KEY (Emp_ID) REFERENCES Instructor(Emp_ID) ON DELETE CASCADE,
    FOREIGN KEY (Subject_ID) REFERENCES Subject(Subject_ID) ON DELETE CASCADE
);
```
- **Composite primary key**: (Emp_ID, Subject_ID) ensures one assignment per instructor per subject
- Cascade delete removes assignments if instructor or subject is deleted
- Represents many-to-many relationship between Instructors and Subjects

---

## Backend Application

### File: `app.py`

The Flask backend provides REST API endpoints for all system operations.

#### Imports and Setup
```python
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
import os
from werkzeug.security import generate_password_hash, check_password_hash

from flask import Flask, jsonify, request, send_from_directory, session
import mysql.connector
from mysql.connector import Error as MySQLError
```
- **contextmanager**: Decorator to create context managers for resource cleanup
- **date, datetime, Decimal**: Handle database date/decimal types
- **os**: Access environment variables for database configuration
- **werkzeug.security**: Hash and verify passwords securely
- **flask modules**: Create web app, return JSON, handle requests, serve files, manage sessions
- **mysql.connector**: Connect to MySQL database
- **MySQLError**: Catch database connection errors

#### Flask App Initialization
```python
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "school_is_secret_key_2026")
FRONTEND_DIR = "templates"
```
- **app = Flask(__name__)**: Creates Flask application instance
- **secret_key**: Used for signing session cookies (from environment or default)
- **FRONTEND_DIR**: Template directory path for HTML files

#### Database Configuration
```python
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME", "school_db"),
    "port": int(os.environ.get("DB_PORT", "3306")),
}
```
- **Dictionary** of database connection settings
- **All values** pull from environment variables with sensible defaults
- Allows deployment flexibility without hardcoding credentials

#### Database Connection Helper
```python
def get_db():
    return mysql.connector.connect(**DB_CONFIG)
```
- **Creates and returns** a new MySQL connection using the DB_CONFIG

#### Context Manager for Database Cursors
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
- **Context manager** ensures proper resource cleanup
- **dictionary=True**: Returns results as dictionaries (column_name: value)
- **try/finally**: Guarantees cursor and connection close even if error occurs
- **yield**: Provides db and cursor to the calling code

#### Value Serialization Helper
```python
def serialize_value(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value
```
- **date/datetime**: Converts to ISO format strings (e.g., "2026-05-02")
- **Decimal**: Converts database DECIMAL type to float for JSON
- **Returns as-is**: If already JSON-serializable
- **Purpose**: Makes database values JSON-compatible

#### Row Serialization Helper
```python
def serialize_rows(rows):
    if rows is None:
        return None
    if isinstance(rows, dict):
        return {key: serialize_value(value) for key, value in rows.items()}
    return [{key: serialize_value(value) for key, value in row.items()} for row in rows]
```
- **None check**: Returns None if no results
- **Single row (dict)**: Serializes dictionary values
- **Multiple rows (list)**: Serializes each row's values
- **Uses serialize_value**: Processes each value individually

#### Generic Database Query Function
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
- **sql**: SQL query with %s placeholders
- **params**: Tuple of query parameters (prevents SQL injection)
- **fetchone**: If True, returns single row; else returns all rows
- **commit**: If True, commits changes and returns None; else returns results
- **Uses context manager**: Ensures cleanup
- **Serializes results**: Makes database types JSON-compatible

#### Error Handler for Database Errors
```python
@app.errorhandler(MySQLError)
def handle_database_error(error):
    return jsonify({
        "ok": False,
        "error": "Database error",
        "detail": str(error),
    }), 500
```
- **@app.errorhandler(MySQLError)**: Catches uncaught MySQL errors globally
- **Returns**: JSON response with error details and HTTP 500 status

---

### Frontend Routes (Serve HTML/CSS)

#### Index/Home Page
```python
@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/index.html")
def index_file():
    return send_from_directory(FRONTEND_DIR, "index.html")
```
- **Two routes**: "/" and "/index.html" both serve the login page
- **Allows flexibility**: Users can navigate to either URL

#### Authentication & Dashboard Routes
```python
@app.route("/signup.html")
def signup_page():
    return send_from_directory(FRONTEND_DIR, "signup.html")

@app.route("/student")
@app.route("/student-dashboard")
@app.route("/student-dashboard.html")
def student_page():
    return send_from_directory(FRONTEND_DIR, "student-dashboard.html")

@app.route("/teacher")
@app.route("/teacher-dashboard")
@app.route("/teacher-dashboard.html")
def teacher_page():
    return send_from_directory(FRONTEND_DIR, "teacher-dashboard.html")

@app.route("/admin-dashboard")
@app.route("/admin-dashboard.html")
def admin_page():
    return send_from_directory(FRONTEND_DIR, "admin-dashboard.html")
```
- **Multiple route decorators**: Allow accessing dashboards via different URLs
- **Each function**: Returns the appropriate HTML file from templates directory

#### Stylesheet Route
```python
@app.route("/style.css")
def style_file():
    return send_from_directory(FRONTEND_DIR, "style.css")
```
- **Serves CSS** from templates directory instead of static files
- **Simplifies deployment**: All frontend assets in one folder

#### Health Check Endpoint
```python
@app.route("/api/health")
def api_health():
    db_query("SELECT 1 AS ok", fetchone=True)
    return jsonify({"ok": True})
```
- **Lightweight endpoint** for monitoring server status
- **Checks database**: Executes simple query to verify connection
- **Returns**: {"ok": True} if server and database are up

---

### Authentication Endpoints

#### Sign In Endpoint
```python
@app.route("/api/signin", methods=["POST"])
def api_signin():
    data = request.get_json(silent=True) or {}
    
    email = data.get("email", "").strip().lower()
    password = data.get("password") or ""
    role = data.get("role", "").strip().lower()
```
- **Gets JSON payload** from request (silent=True suppresses parse errors)
- **Extracts fields**: email (lowercase), password, role
- **silent=True**: Returns empty dict if not valid JSON

#### Input Validation
```python
    if not email or not password:
        return jsonify({"ok": False, "error": "Missing credentials"}), 400
    
    if role and role not in ("student", "teacher", "admin"):
        return jsonify({"ok": False, "error": "Invalid role"}), 400
```
- **Validates email/password**: Both required
- **Validates role**: If provided, must be valid (optional field)
- **Returns 400**: HTTP bad request for validation failures

#### User Lookup and Password Verification
```python
    user = db_query(
        "SELECT * FROM Users WHERE Email = %s",
        (email,), fetchone=True
    )
    
    if not user:
        return jsonify({"ok": False, "error": "User not found"}), 404
    
    if not check_password_hash(user["Password_Hash"], password):
        return jsonify({"ok": False, "error": "Wrong password"}), 401
```
- **Queries Users table** by email
- **404**: User doesn't exist
- **check_password_hash**: Securely verifies password against hash
- **401**: Password incorrect

#### Role Verification
```python
    if role and user["Role"] != role:
        return jsonify({"ok": False, "error": f"This account is registered as {user['Role']}"}), 403
```
- **If role specified**: Verify account matches requested role
- **403**: Forbidden - user trying to log in as wrong role

#### Admin Session Creation
```python
    if user["Role"] == "admin":
        session["user"] = {
            "id": user["User_ID"],
            "name": user["Full_Name"],
            "role": "admin"
        }
        return jsonify({"ok": True, "user": session["user"]})
```
- **Admin special case**: No linked entity needed
- **Sets session**: Stores user data in encrypted session cookie
- **Returns session data**: Including user ID, name, role

#### Student Entity Linking
```python
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
```
- **Queries Student table** for matching User_ID
- **500 error**: If no linked student (data integrity issue)
- **Sets session**: Uses Student_ID (not User_ID) for student sessions

#### Teacher/Employee Entity Linking
```python
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
- **Queries Employee table** for teacher/admin
- **500 error**: If no linked employee
- **Sets session**: Uses Emp_ID for teacher/admin sessions
- **Preserves role**: Maintains teacher or admin role value

#### Sign Up Endpoint
```python
@app.route("/api/signup", methods=["POST"])
def api_signup():
    data = request.get_json(silent=True) or {}
    
    role     = data.get("role", "").strip().lower()
    name     = data.get("name", "").strip()
    email    = data.get("email", "").strip().lower()
    id_      = str(data.get("id", "")).strip()
    password = data.get("password") or ""
```
- **Extracts fields**: role, full name, email, ID, password

#### Role and Password Validation
```python
    if role not in ("student", "teacher", "admin"):
        return jsonify({"ok": False, "error": "Role must be student, teacher, or admin"}), 400
    
    if not all([name, email, password]) or len(password) < 6:
        return jsonify({"ok": False, "error": "Invalid input"}), 400
```
- **Role validation**: Must be one of three types
- **Required fields**: name, email, password
- **Password minimum**: 6 characters

#### ID Validation (except admin)
```python
    id_int = None
    if role != "admin":
        if not id_:
            return jsonify({"ok": False, "error": "ID is required"}), 400
        try:
            id_int = int(id_)
        except ValueError:
            return jsonify({"ok": False, "error": "ID must be numeric"}), 400
```
- **Admin doesn't need ID**: Uses auto-increment User_ID
- **Student/Teacher require ID**: Must be numeric
- **Converts to integer**: For database insertion

#### Name Splitting
```python
    fname, *lname_parts = name.split(" ")
    lname = " ".join(lname_parts) or "-"
```
- **Splits full name**: First word is fname, rest is lname
- **Multi-part last names**: Handled by joining
- **Default "-"**: If no last name provided

#### Password Hashing
```python
    hashed = generate_password_hash(password)
```
- **Hashes password**: Uses Werkzeug's secure hashing (salted)
- **Never stores plain**: Only stores hash for security

#### Transaction Block
```python
    try:
        with db_cursor() as (db, cursor):
            cursor.execute(
                """INSERT INTO Users (Full_Name, Email, Password_Hash, Role)
                   VALUES (%s, %s, %s, %s)""",
                (name, email, hashed, role)
            )
            user_id = cursor.lastrowid
```
- **Creates Users entry**: Inserts new user with role
- **Gets auto_increment ID**: lastrowid for the new user

#### Student Registration Branch
```python
            if role == "student":
                cursor.execute(
                    """INSERT INTO Student
                       (Student_ID, Fname, Lname, Student_Email, User_ID,
                        Level, Birth_Date, City, Street, Building_Num)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        id_int, fname, lname, email, user_id,
                        data.get("level") or None,
                        data.get("birth_date") or None,
                        data.get("city") or None,
                        data.get("street") or None,
                        data.get("building_num") or None,
                    )
                )
                session_id = id_int
```
- **Creates Student entry**: Uses provided Student_ID
- **Links to Users**: Via user_id foreign key
- **Optional fields**: Level, birth date, address (set to None if not provided)
- **session_id = id_int**: Session will use Student_ID

#### Teacher Registration Branch
```python
            elif role == "teacher":
                cursor.execute("SELECT Dept_ID FROM Department LIMIT 1")
                dept = cursor.fetchone()
                if not dept:
                    db.rollback()
                    return jsonify({"ok": False, "error": "No departments exist"}), 400
                
                cursor.execute(
                    """INSERT INTO Employee
                       (Emp_ID, Emp_FName, Emp_Lname, Dept_ID, User_ID, Employment_Date)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (
                        id_int, fname, lname,
                        dept["Dept_ID"], user_id,
                        data.get("employment_date") or None,
                    )
                )
                cursor.execute(
                    "INSERT INTO Instructor (Emp_ID) VALUES (%s)",
                    (id_int,)
                )
                session_id = id_int
```
- **Requires existing department**: Assigns to first available
- **Rollback if no depts**: Cancels transaction to maintain consistency
- **Creates Employee entry**: For teacher records
- **Creates Instructor entry**: Specialization of Employee
- **session_id = id_int**: Session will use Emp_ID

#### Admin Registration Branch
```python
            else:
                session_id = user_id
```
- **Admin simple case**: No linked entity needed
- **session_id = user_id**: Session uses User_ID for admin

#### Commit and Session Setup
```python
            db.commit()
            session["user"] = {"id": session_id, "name": name, "role": role}
```
- **Commits transaction**: All inserts applied atomically
- **Sets session**: Logs user in immediately after signup

#### Integrity Error Handling
```python
    except mysql.connector.IntegrityError as e:
        err = str(e)
        if "Duplicate entry" in err:
            if "Email" in err:
                return jsonify({"ok": False, "error": "That email is already registered."}), 409
            return jsonify({"ok": False, "error": "That ID is already taken."}), 409
        return jsonify({"ok": False, "error": err}), 409
    
    return jsonify({"ok": True, "user": session["user"]})
```
- **IntegrityError**: Catches database constraint violations
- **Duplicate email**: Returns specific error message
- **Duplicate ID**: Returns specific error message
- **Other integrity errors**: Returns generic error
- **409 Conflict**: HTTP status for duplicate/conflict
- **Success response**: Returns user session data

#### Sign Out Endpoint
```python
@app.route("/api/signout", methods=["POST"])
def api_signout():
    session.clear()
    return jsonify({"ok": True})
```
- **Clears session**: Removes all session data (logs user out)
- **Returns success**: Always succeeds

#### Get Current User Endpoint
```python
@app.route("/api/me")
def api_me():
    user = session.get("user")
    if not user:
        return jsonify({"ok": False}), 401
    return jsonify({"ok": True, "user": user})
```
- **Gets session user**: If logged in
- **401 Unauthorized**: If no session
- **Returns user data**: Current session user info

---

### Dashboard Statistics Endpoint

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
- **Counts each entity type**: Queries COUNT(*) for system overview
- **Recent students**: Last 5 students added (ordered descending)
- **Returns**: Counts and recent students for dashboard display

---

### Student Management Endpoints

#### List Students
```python
@app.route("/api/students", methods=["GET"])
def api_students_list():
    rows = db_query("SELECT * FROM Student ORDER BY Student_ID")
    for r in rows:
        if r.get("Birth_Date"):
            r["Birth_Date"] = str(r["Birth_Date"])
    return jsonify({"ok": True, "students": rows})
```
- **Gets all students**: Ordered by Student_ID
- **Converts dates**: Ensures Birth_Date is string (not datetime object)
- **Returns all fields**: Complete student records

#### Add Student
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
- **Required fields**: student_id, fname, lname
- **Optional fields**: level, birth_date, email, address
- **Handles duplicates**: 409 if student_id already exists
- **Commits immediately**: Uses commit=True

#### Edit Student
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
- **URL parameter**: student_id extracted from URL
- **Updates all fields**: Accepts any subset of fields
- **Handles optional fields**: None if not provided

#### Delete Student
```python
@app.route("/api/students/<int:student_id>", methods=["DELETE"])
def api_students_delete(student_id):
    db_query("DELETE FROM Student WHERE Student_ID = %s", (student_id,), commit=True)
    return jsonify({"ok": True, "message": "Student deleted."})
```
- **Cascade delete**: Removes related Studies records (via foreign key)
- **Simple deletion**: One query for direct deletion

#### Get Student's Courses
```python
@app.route("/api/students/<int:student_id>/courses")
def api_student_courses(student_id):
    rows = db_query(
        """SELECT
               s.Subject_ID, s.Subject_Name, s.Subject_Level, s.Subject_Slots,
               s.Classroom_ID,
               c.Classroom_Building, c.Classroom_Floor,
               CONCAT(e.Emp_FName, ' ', e.Emp_Lname) AS Instructor_Name
           FROM Studies st
           JOIN Subject s   ON st.Subject_ID = s.Subject_ID
           LEFT JOIN Classroom c  ON s.Classroom_ID = c.Classroom_ID
           LEFT JOIN Teaches t    ON t.Subject_ID = s.Subject_ID
           LEFT JOIN Employee e   ON e.Emp_ID = t.Emp_ID
           WHERE st.Student_ID = %s""",
        (student_id,)
    )
    return jsonify({"ok": True, "courses": rows})
```
- **Complex join query**: Gathers course and classroom info
- **LEFT JOINs**: Optional instructor and classroom info
- **CONCAT**: Combines first/last names
- **Returns all course details**: Ready for display

#### Get Student's Grades
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
- **Joins Studies and Subject**: Gets subject names with grades
- **Simple columns**: Only subject name and grade
- **Used for grade display**: Lightweight query

---

### Grade Management Endpoints

#### Upsert Grade (Insert or Update)
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
- **Validates range**: Grade must be 0-100
- **ON DUPLICATE KEY UPDATE**: MySQL-specific upsert
- **If exists**: Updates grade; if not, inserts
- **Handles both cases**: Single operation

---

### Instructor Management Endpoints

#### List Instructors
```python
@app.route("/api/instructors", methods=["GET"])
def api_instructors_list():
    rows = db_query("""
        SELECT i.Emp_ID, e.Emp_FName, e.Emp_Lname, i.Qualification,
               d.Dept_Name, e.Employment_Date
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
- **Joins multiple tables**: Gets instructor, employee, and department info
- **Date conversion**: Ensures Employment_Date is string
- **Ordered**: By Emp_ID for consistency

#### Add Instructor
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
- **Two inserts**: First to Employee, then to Instructor
- **Links properly**: Uses emp_id for both
- **Optional fields**: employment_date, qualification
- **Handles duplicates**: 409 if emp_id exists

#### Delete Instructor
```python
@app.route("/api/instructors/<int:emp_id>", methods=["DELETE"])
def api_instructors_delete(emp_id):
    db_query("DELETE FROM Employee WHERE Emp_ID = %s", (emp_id,), commit=True)
    return jsonify({"ok": True, "message": "Instructor deleted."})
```
- **Cascade delete**: Removes Instructor and Teaches records
- **Single delete**: Via foreign key constraints

---

### Employee Management Endpoints

#### List Employees
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
- **Self-join for supervisor**: LEFT JOIN to Employee s for supervisor info
- **Department info**: Joins Department table
- **Optional supervisor**: LEFT JOIN handles null supervisor_id
- **Alias supervisor name**: Sup_FName, Sup_Lname

#### Add Employee
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
- **All Employee fields**: Required: emp_id, names, dept_id
- **Optional fields**: employment_date, supervisor_id

#### Delete Employee
```python
@app.route("/api/employees/<int:emp_id>", methods=["DELETE"])
def api_employees_delete(emp_id):
    db_query("DELETE FROM Employee WHERE Emp_ID = %s", (emp_id,), commit=True)
    return jsonify({"ok": True, "message": "Employee deleted."})
```
- **Cascade delete**: Removes related Instructor, Teaches, Employee_Phone records

---

### Subject Management Endpoints

#### List Subjects
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
- **Includes classroom info**: Building and floor via LEFT JOIN
- **Ordered**: By Subject_ID

#### Add Subject
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
- **Required fields**: subject_id, subject_name
- **Optional fields**: subject_level, subject_slots, classroom_id

#### Delete Subject
```python
@app.route("/api/subjects/<int:subject_id>", methods=["DELETE"])
def api_subjects_delete(subject_id):
    db_query("DELETE FROM Subject WHERE Subject_ID = %s", (subject_id,), commit=True)
    return jsonify({"ok": True, "message": "Subject deleted."})
```
- **Cascade delete**: Removes Studies and Teaches records

---

### Classroom Management Endpoints

#### List Classrooms
```python
@app.route("/api/classrooms", methods=["GET"])
def api_classrooms_list():
    rows = db_query("SELECT * FROM Classroom ORDER BY Classroom_ID")
    return jsonify({"ok": True, "classrooms": rows})
```
- **All classrooms**: Simple query, ordered by ID

#### Add Classroom
```python
@app.route("/api/classrooms", methods=["POST"])
def api_classrooms_add():
    d = request.get_json(silent=True) or {}
    try:
        db_query(
            """INSERT INTO Classroom (Classroom_ID, Classroom_Level, Classroom_Capacity, Classroom_Building, Classroom_Floor)
               VALUES (%s, %s, %s, %s, %s)""",
            (d["classroom_id"],
             d.get("classroom_level") or None,
             d.get("classroom_capacity") or None,
             d.get("classroom_building") or None,
             d.get("classroom_floor") or None),
            commit=True
        )
    except mysql.connector.IntegrityError as e:
        return jsonify({"ok": False, "error": str(e)}), 409
    return jsonify({"ok": True, "message": "Classroom added!"})
```
- **Required field**: classroom_id
- **Optional fields**: level, capacity, building, floor

#### Delete Classroom
```python
@app.route("/api/classrooms/<int:classroom_id>", methods=["DELETE"])
def api_classrooms_delete(classroom_id):
    db_query("DELETE FROM Classroom WHERE Classroom_ID = %s", (classroom_id,), commit=True)
    return jsonify({"ok": True, "message": "Classroom deleted."})
```
- **Cascade delete**: Removes Subject records using this classroom

---

### Department Management Endpoints

#### List Departments
```python
@app.route("/api/departments", methods=["GET"])
def api_departments_list():
    rows = db_query("SELECT * FROM Department ORDER BY Dept_ID")
    return jsonify({"ok": True, "departments": rows})
```
- **All departments**: Simple query

#### Add Department
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
- **Required fields**: dept_id, dept_name
- **Optional field**: dept_head

#### Delete Department
```python
@app.route("/api/departments/<int:dept_id>", methods=["DELETE"])
def api_departments_delete(dept_id):
    db_query("DELETE FROM Department WHERE Dept_ID = %s", (dept_id,), commit=True)
    return jsonify({"ok": True, "message": "Department deleted."})
```
- **Cascade delete**: Removes Employee records (via foreign key)

---

### Admin Users Endpoint

```python
@app.route("/api/users/admins", methods=["GET"])
def api_users_admins():
    rows = db_query(
        "SELECT User_ID, Full_Name, Email, Created_At FROM Users WHERE Role = 'admin' ORDER BY User_ID"
    )
    return jsonify({"ok": True, "admins": rows})
```
- **Filters by role**: Only admin users
- **Includes metadata**: User_ID, name, email, creation time

---

### Course Assignment Endpoints (Teaches Relationship)

#### List Assignments
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
- **Joins three tables**: Teaches, Subject, Employee
- **Includes names**: Subject and instructor names
- **Ordered**: By emp_id then subject_id

#### Assign Course to Instructor
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
    except mysql.connector.IntegrityError as e:
        return jsonify({"ok": False, "error": "Already assigned or invalid IDs."}), 409
    return jsonify({"ok": True, "message": "Course assigned."})
```
- **Validates input**: Both emp_id and subject_id required
- **Prevents duplicates**: Composite primary key prevents duplicate assignments
- **409 Conflict**: If already assigned

#### Unassign Course from Instructor
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
- **Validates input**: Both IDs required
- **Simple deletion**: Removes one assignment

---

### Teacher Query Endpoints

#### Get Teacher's Subjects
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
- **Gets assigned subjects**: For a specific teacher
- **Joins via Teaches**: Gets all subject info

#### Get Teacher's Students
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
- **Complex join**: Studies → Student + Teaches
- **DISTINCT**: Avoids duplicates if student in multiple teacher's courses
- **Gets all students**: For a specific teacher's courses
- **Ordered**: By Student_ID

---

### Application Entry Point

```python
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
```
- **Only runs**: When script is executed directly (not imported)
- **host 127.0.0.1**: Localhost only (development)
- **port 5000**: Flask default port
- **Starts development server**: Auto-reloads on code changes

---

## Frontend Templates

### File: `templates/index.html` - Login Page

#### HTML Structure
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NRC School - Login</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="page-wrapper">
        <div class="login-card">
            <h2>NRC School Information System</h2>
            <h3>Login to your account</h3>
```
- **UTF-8 charset**: Supports all characters
- **Viewport meta**: Enables responsive design
- **Title**: Browser tab and search engines
- **Stylesheet link**: External CSS file

#### Role Selection
```html
            <div class="role-selection">
                <label>Login As:</label>
                <div class="role-buttons">
                    <button type="button" class="role-btn active" data-role="student">Student</button>
                    <button type="button" class="role-btn" data-role="teacher">Teacher</button>
                    <button type="button" class="role-btn" data-role="admin">Admin</button>
                </div>
            </div>
```
- **Three role buttons**: Default active is student
- **data-role attribute**: Stores role value for JavaScript
- **User can switch roles**: Via button clicks

#### Login Form
```html
            <div class="input-group">
                <label for="email">Email:</label>
                <input type="email" id="email" placeholder="example@email.com">
            </div>

            <div class="input-group">
                <label for="password">Password:</label>
                <input type="password" id="password" placeholder="Enter your password">
            </div>

            <button class="login-btn" id="login-btn">Login</button>
```
- **Email input**: type="email" for validation
- **Password input**: Hides characters
- **ID selectors**: For JavaScript manipulation
- **Login button**: Triggers sign-in API call

#### Navigation Links
```html
            <h3>Not registered?</h3>
            <a href="signup.html" class="register-btn">Register Here</a>
```
- **Link to signup**: If user needs to create account

#### JavaScript: Role Selection
```javascript
        const DASHBOARDS = {
            student: "student-dashboard.html",
            teacher: "teacher-dashboard.html",
            admin:   "admin-dashboard.html"
        };

        let selectedRole = "student";

        document.querySelectorAll(".role-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                document.querySelectorAll(".role-btn").forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                selectedRole = btn.dataset.role;
            });
        });
```
- **DASHBOARDS mapping**: Where to redirect after login
- **selectedRole state**: Tracks which role is selected
- **Click handlers**: Toggle "active" class and update role
- **data.role attribute**: Gets role from button

#### JavaScript: Message Display
```javascript
        function showMessage(msg, type = "error") {
            const el = document.getElementById("message");
            el.textContent = msg;
            el.className = "form-message " + type;
        }
```
- **Updates message element**: With text and type
- **type parameter**: "error" or "success" for styling

#### JavaScript: Login Handler
```javascript
        document.getElementById("login-btn").addEventListener("click", async () => {
            const email    = document.getElementById("email").value.trim();
            const password = document.getElementById("password").value;

            if (!email || !password) {
                showMessage("Please enter your email and password.");
                return;
            }

            const btn = document.getElementById("login-btn");
            btn.disabled = true;
            btn.textContent = "Logging in...";

            try {
                const res = await fetch("/api/signin", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, password, role: selectedRole })
                });
                const data = await res.json();

                if (!res.ok || !data.ok) {
                    showMessage(data.error || "Login failed.");
                    return;
                }

                showMessage("Login successful! Redirecting...", "success");
                window.location.href = DASHBOARDS[data.user.role];

            } catch (err) {
                showMessage("Cannot connect to server. Is Flask running?");
            } finally {
                btn.disabled = false;
                btn.textContent = "Login";
            }
        });
```
- **Gets email/password**: From input fields
- **Client validation**: Requires both fields
- **Disables button**: Prevents multiple submissions
- **Fetches /api/signin**: Sends POST request
- **Handles response**: Checks ok and data.ok flags
- **Redirects on success**: To appropriate dashboard
- **Error handling**: Shows error messages or network issues
- **Re-enables button**: In finally block (always runs)

---

### File: `templates/signup.html` - Registration Page

#### Structure Overview
```html
            <div id="form-student">
                <!-- Student registration fields -->
            </div>

            <div id="form-teacher" style="display:none">
                <!-- Teacher registration fields -->
            </div>

            <div id="form-admin" style="display:none">
                <!-- Admin registration fields -->
            </div>
```
- **Three form sections**: One for each role
- **Initially hidden**: Only student form visible

#### Student Registration Form
```html
                <div class="input-group">
                    <label>Student ID:</label>
                    <input type="number" id="s-id" placeholder="Enter your student ID">
                </div>
                <div class="input-group">
                    <label>First Name:</label>
                    <input type="text" id="s-fname" placeholder="First name">
                </div>
                <!-- ... more fields ... -->
                <button class="login-btn" id="btn-student">Create Student Account</button>
```
- **All required fields**: ID, first name, last name, email, password
- **Optional fields**: Level, birth date, address
- **Unique button**: For student registration

#### JavaScript: Role Switch Function
```javascript
        function switchRole(role) {
            selectedRole = role;
            document.querySelectorAll(".role-btn").forEach(b =>
                b.classList.toggle("active", b.dataset.role === role)
            );
            document.getElementById("form-student").style.display = role === "student" ? "block" : "none";
            document.getElementById("form-teacher").style.display = role === "teacher" ? "block" : "none";
            document.getElementById("form-admin").style.display   = role === "admin"   ? "block" : "none";
            showMessage("");
        }

        document.querySelectorAll(".role-btn").forEach(btn =>
            btn.addEventListener("click", () => switchRole(btn.dataset.role))
        );
```
- **Updates selectedRole**: Global state
- **Toggles active class**: On role buttons
- **Shows/hides forms**: Based on selected role
- **Clears messages**: When switching roles
- **Event listeners**: Trigger switch on button click

#### JavaScript: Generic Sign-Up Function
```javascript
        async function submitSignup(payload) {
            try {
                const res = await fetch("/api/signup", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (!res.ok || !data.ok) {
                    showMessage(data.error || "Signup failed.");
                    return false;
                }
                showMessage("Account created! Redirecting...", "success");
                setTimeout(() => window.location.href = DASHBOARDS[data.user.role], 800);
                return true;
            } catch {
                showMessage("Cannot connect to server. Is Flask running?");
                return false;
            }
        }
```
- **Generic function**: Used by all role types
- **Posts to /api/signup**: With role-specific payload
- **Handles errors**: Shows error messages
- **Redirects on success**: After 800ms delay
- **Catches network errors**: Shows connection error

#### JavaScript: Student Sign-Up Handler
```javascript
        document.getElementById("btn-student").addEventListener("click", async () => {
            const id       = document.getElementById("s-id").value.trim();
            const fname    = document.getElementById("s-fname").value.trim();
            const lname    = document.getElementById("s-lname").value.trim();
            const email    = document.getElementById("s-email").value.trim();
            const password = document.getElementById("s-password").value;

            if (!id || !fname || !lname || !email || !password) {
                showMessage("ID, name, email, and password are required."); return;
            }
            if (password.length < 6) {
                showMessage("Password must be at least 6 characters."); return;
            }

            const btn = document.getElementById("btn-student");
            btn.disabled = true; btn.textContent = "Creating...";
            await submitSignup({
                role: "student",
                name: fname + " " + lname,
                email, password,
                id,
                level:        document.getElementById("s-level").value.trim() || null,
                birth_date:   document.getElementById("s-birthdate").value || null,
                city:         document.getElementById("s-city").value.trim() || null,
                street:       document.getElementById("s-street").value.trim() || null,
                building_num: document.getElementById("s-building").value.trim() || null,
            });
```
- **Validates required fields**: All must be provided
- **Validates password**: Minimum 6 characters
- **Disables button**: During submission
- **Constructs payload**: Combines first and last names
- **Includes optional fields**: Sets to null if empty
- **Calls submitSignup**: With role and data

---

### File: `templates/student-dashboard.html` - Student Dashboard

#### Page Structure
```html
<body>
    <h1>NRC School Information System</h1>
<div class="dashboard-page">
    <div class="dashboard-header">
        <!-- Welcome and logout -->
    </div>

    <div class="dashboard-grid">
        <!-- Cards for courses, grades, schedule -->
    </div>
</div>

<!-- Overlay panels for each section -->
<div class="panel-overlay" id="panel-courses">
    <!-- Courses panel content -->
</div>
```
- **Dashboard page**: Main container
- **Header section**: Welcome message and logout
- **Grid section**: Cards for features
- **Overlay panels**: Show detailed data

#### Dashboard Grid Cards
```html
        <section class="dashboard-card" id="card-courses">
            <h2>📚 My Courses</h2>
            <p>View your enrolled courses and class details.</p>
            <p class="card-hint">Click to view</p>
        </section>
        <section class="dashboard-card" id="card-grades">
            <h2>🎓 Grades</h2>
            <p>Check your latest grades and academic progress.</p>
            <p class="card-hint">Click to view</p>
        </section>
        <section class="dashboard-card" id="card-schedule">
            <h2>📅 Schedule</h2>
            <p>See your subjects, rooms, and class levels.</p>
            <p class="card-hint">Click to view</p>
        </section>
```
- **Three main features**: Courses, grades, schedule
- **Emoji icons**: Visual indicators
- **Card hints**: "Click to view" user guidance
- **Clickable cards**: Each has event listener

#### Panel Overlay Structure
```html
<div class="panel-overlay" id="panel-courses">
    <div class="panel">
        <button class="close-btn" data-close="panel-courses">✕</button>
        <h2>📚 My Courses</h2>
        <div id="courses-body"><p class="loading-msg">Loading...</p></div>
    </div>
</div>
```
- **Overlay div**: Semi-transparent background (modal)
- **Panel div**: Content container (modal dialog)
- **Close button**: data attribute stores panel ID
- **Body div**: Loading message initially, then data

#### JavaScript: Authentication Check
```javascript
    let studentId = null;

    fetch("/api/me")
        .then(r => r.json())
        .then(data => {
            if (!data.ok || data.user.role !== "student") {
                window.location.href = "index.html";
                return;
            }
            studentId = data.user.id;
            document.getElementById("welcome-msg").textContent = "Welcome back, " + data.user.name;
        })
        .catch(() => window.location.href = "index.html");
```
- **Calls /api/me**: Checks if logged in
- **Validates role**: Redirects if not student
- **Gets studentId**: Stores for API calls
- **Shows welcome**: Personalized greeting
- **Error handling**: Redirect on network error

#### JavaScript: Logout Handler
```javascript
    document.getElementById("logout-btn").addEventListener("click", async () => {
        await fetch("/api/signout", { method: "POST" });
        window.location.href = "index.html";
    });
```
- **Posts to /api/signout**: Clears session
- **Redirects to login**: After logout

#### JavaScript: Panel Helpers
```javascript
    function openPanel(panelId) {
        document.getElementById(panelId).classList.add("open");
        document.body.style.overflow = "hidden";
    }
    function closePanel(panelId) {
        document.getElementById(panelId).classList.remove("open");
        document.body.style.overflow = "";
    }

    document.querySelectorAll(".close-btn").forEach(btn => {
        btn.addEventListener("click", () => closePanel(btn.dataset.close));
    });
    document.querySelectorAll(".panel-overlay").forEach(overlay => {
        overlay.addEventListener("click", e => {
            if (e.target === overlay) closePanel(overlay.id);
        });
    });
```
- **openPanel()**: Shows overlay with "open" class, hides scroll
- **closePanel()**: Hides overlay, restores scroll
- **Close buttons**: Use data-close attribute
- **Click outside**: Closes panel if clicking background

#### JavaScript: Grade Helper Functions
```javascript
    function gradeClass(g) {
        if (g === null || g === undefined) return "grade-na";
        if (g >= 90) return "grade-a";
        if (g >= 80) return "grade-b";
        if (g >= 70) return "grade-c";
        if (g >= 60) return "grade-d";
        return "grade-f";
    }
    function gradeLabel(g) {
        if (g === null || g === undefined) return "N/A";
        if (g >= 90) return "A";
        if (g >= 80) return "B";
        if (g >= 70) return "C";
        if (g >= 60) return "D";
        return "F";
    }
```
- **gradeClass()**: Returns CSS class for styling
- **gradeLabel()**: Returns letter grade
- **Scale**: 90+=A, 80+=B, 70+=C, 60+=D, <60=F

#### JavaScript: Courses Panel Handler
```javascript
    document.getElementById("card-courses").addEventListener("click", async () => {
        openPanel("panel-courses");
        const body = document.getElementById("courses-body");
        body.innerHTML = '<p class="loading-msg">Loading...</p>';

        try {
            const res  = await fetch(`/api/students/${studentId}/courses`);
            const data = await res.json();

            if (!data.ok || !data.courses.length) {
                body.innerHTML = '<p class="empty-msg">No courses enrolled yet.</p>';
                return;
            }

            body.innerHTML = `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Course Name</th>
                            <th>Level</th>
                            <th>Instructor</th>
                            <th>Slots</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.courses.map((c, i) => `
                            <tr>
                                <td>${i + 1}</td>
                                <td>${c.Subject_Name}</td>
                                <td>${c.Subject_Level || '—'}</td>
                                <td>${c.Instructor_Name || '—'}</td>
                                <td>${c.Subject_Slots || '—'}</td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>`;
        } catch {
            body.innerHTML = '<p class="empty-msg">Failed to load courses.</p>';
        }
    });
```
- **Click handler**: Opens courses panel
- **Loading state**: Shows loading message initially
- **Fetches data**: From /api/students/ID/courses
- **Handles empty state**: Shows message if no courses
- **Renders table**: Dynamically generates HTML with map()
- **Error handling**: Shows failure message
- **Data mapping**: Displays all course details

#### JavaScript: Grades Panel Handler
```javascript
    document.getElementById("card-grades").addEventListener("click", async () => {
        openPanel("panel-grades");
        const body = document.getElementById("grades-body");
        body.innerHTML = '<p class="loading-msg">Loading...</p>';

        try {
            const res  = await fetch(`/api/students/${studentId}/grades`);
            const data = await res.json();

            if (!data.ok || !data.grades.length) {
                body.innerHTML = '<p class="empty-msg">No grades recorded yet.</p>';
                return;
            }

            const avg = (data.grades.reduce((s, g) => s + (g.Grades ?? 0), 0) / data.grades.length).toFixed(1);

            body.innerHTML = `
                <p style="margin-bottom:16px; color:#5f6b7a;">
                    Overall Average: <strong style="color:#111413">${avg}</strong>
                </p>
                <table class="data-table">
                    <thead>
                        <tr><th>Subject</th><th>Score</th><th>Grade</th></tr>
                    </thead>
                    <tbody>
                        ${data.grades.map(g => `
                            <tr>
                                <td>${g.Subject_Name}</td>
                                <td>${g.Grades ?? '—'}</td>
                                <td>
                                    <span class="grade-badge ${gradeClass(g.Grades)}">
                                        ${gradeLabel(g.Grades)}
                                    </span>
                                </td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>`;
        } catch {
            body.innerHTML = '<p class="empty-msg">Failed to load grades.</p>';
        }
    });
```
- **Calculates average**: Uses reduce() to sum grades, divides by count
- **Nullish coalescing**: ?? 0 handles missing grades
- **toFixed(1)**: Rounds to 1 decimal place
- **Grade badges**: Colored spans with letter grade
- **Styled table**: Shows all grades with averages

#### JavaScript: Schedule Panel Handler
```javascript
    document.getElementById("card-schedule").addEventListener("click", async () => {
        openPanel("panel-schedule");
        const body = document.getElementById("schedule-body");
        body.innerHTML = '<p class="loading-msg">Loading...</p>';

        try {
            const res  = await fetch(`/api/students/${studentId}/courses`);
            const data = await res.json();

            if (!data.ok || !data.courses.length) {
                body.innerHTML = '<p class="empty-msg">No schedule available yet.</p>';
                return;
            }

            body.innerHTML = `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Course</th>
                            <th>Level</th>
                            <th>Building</th>
                            <th>Floor</th>
                            <th>Room</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.courses.map(c => `
                            <tr>
                                <td>${c.Subject_Name}</td>
                                <td>${c.Subject_Level || '—'}</td>
                                <td>${c.Classroom_Building || '—'}</td>
                                <td>${c.Classroom_Floor || '—'}</td>
                                <td>${c.Classroom_ID ? '#' + c.Classroom_ID : '—'}</td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>`;
        } catch {
            body.innerHTML = '<p class="empty-msg">Failed to load schedule.</p>';
        }
    });
```
- **Reuses courses API**: Same endpoint, different display
- **Shows classroom info**: Building, floor, room number
- **Format room**: Adds '#' prefix to Classroom_ID

---

### File: `templates/teacher-dashboard.html` - Teacher Dashboard

#### Basic Structure
```html
<body>
    <div class="dashboard-page">
        <div class="dashboard-header">
            <div>
                <p class="dashboard-kicker">NRC School Information System</p>
                <h1>Teacher Dashboard</h1>
                <p id="welcome-msg"></p>
            </div>
            <button class="logout-link" id="logout-btn">Logout</button>
        </div>

        <div class="dashboard-grid">
            <section class="dashboard-card">
                <h2>My Classes</h2>
                <p>Manage subjects, classrooms, and assigned groups.</p>
            </section>
            <section class="dashboard-card">
                <h2>Students</h2>
                <p>Review enrolled students and class performance.</p>
            </section>
            <section class="dashboard-card">
                <h2>Grades</h2>
                <p>Prepare, update, and publish student grades.</p>
            </section>
        </div>
    </div>
```
- **Dashboard page**: Main container
- **Header**: Title and logout
- **Grid**: Three feature cards (basic, no full implementation)

#### JavaScript: Auth and Basic Functionality
```javascript
    fetch("/api/me")
        .then(res => res.json())
        .then(data => {
            if (!data.ok || data.user.role !== "teacher") {
                window.location.href = "index.html";
                return;
            }
            document.getElementById("welcome-msg").textContent = "Welcome, " + data.user.name;
        })
        .catch(() => window.location.href = "index.html");

    document.getElementById("logout-btn").addEventListener("click", async () => {
        await fetch("/api/signout", { method: "POST" });
        window.location.href = "index.html";
    });
```
- **Checks auth**: Verifies teacher role
- **Redirects if not teacher**: To login page
- **Shows welcome**: Personalized greeting
- **Logout handler**: Calls /api/signout and redirects

---

### File: `templates/admin-dashboard.html` - Admin Dashboard

#### Header and Grid
```html
    <div class="dashboard-header">
        <div>
            <p class="dashboard-kicker">NRC School Information System</p>
            <h1>Admin Dashboard</h1>
            <p id="welcome-msg" style="color:#5f6b7a; margin-top:4px;"></p>
        </div>
        <button class="logout-link" id="logout-btn">Logout</button>
    </div>

    <div class="dashboard-grid">
        <section class="dashboard-card" id="card-instructors">
            <h2>👨‍🏫 Instructors</h2>
            <p>View, add, and remove instructors. Assign courses to each one.</p>
            <p class="card-hint">Click to manage</p>
        </section>
        <section class="dashboard-card" id="card-admins">
            <h2>🛡️ Admins</h2>
            <p>View all admin accounts registered in the system.</p>
            <p class="card-hint">Click to manage</p>
        </section>
        <section class="dashboard-card" id="card-courses">
            <h2>📚 Course Assignments</h2>
            <p>Assign or remove courses from any instructor at a glance.</p>
            <p class="card-hint">Click to manage</p>
        </section>
    </div>
```
- **Three admin features**: Instructors, admins, course assignments
- **Card clickable**: Each opens respective panel

#### Instructors Management Panel
```html
<div class="panel-overlay" id="panel-instructors">
    <div class="panel">
        <button class="close-btn" data-close="panel-instructors">✕</button>
        <h2>👨‍🏫 Manage Instructors</h2>
        <p class="panel-msg" id="msg-instructors"></p>

        <div class="form-row">
            <div class="input-group">
                <label>Employee ID</label>
                <input type="number" id="i-id" placeholder="e.g. 201">
            </div>
            <!-- ... more fields ... -->
            <button class="btn-add" id="btn-add-instructor">+ Add</button>
        </div>

        <div id="instructors-body"><p class="loading-msg">Loading...</p></div>
    </div>
</div>
```
- **Form fields**: ID, names, department, qualification
- **Table**: Lists all instructors
- **Delete buttons**: For each instructor

#### JavaScript: Auth Check
```javascript
fetch("/api/me")
    .then(r => r.json())
    .then(d => {
        if (!d.ok || d.user.role !== "admin") { window.location.href = "index.html"; return; }
        document.getElementById("welcome-msg").textContent = "Welcome back, " + d.user.name;
    })
    .catch(() => window.location.href = "index.html");
```
- **Validates admin role**: Redirects if not
- **Shows welcome**: With user name

#### JavaScript: Panel Management Functions
```javascript
function openPanel(id)  { document.getElementById(id).classList.add("open");    document.body.style.overflow = "hidden"; }
function closePanel(id) { document.getElementById(id).classList.remove("open"); document.body.style.overflow = ""; }

document.querySelectorAll(".close-btn").forEach(b => b.addEventListener("click", () => closePanel(b.dataset.close)));
document.querySelectorAll(".panel-overlay").forEach(o => o.addEventListener("click", e => { if (e.target === o) closePanel(o.id); }));

function showMsg(elId, msg, type = "error") {
    const el = document.getElementById(elId);
    el.textContent = msg;
    el.className = "panel-msg " + type;
    if (type === "success") setTimeout(() => el.textContent = "", 3000);
}
```
- **openPanel/closePanel()**: Toggle overlay visibility
- **Close button handlers**: Click to close
- **Overlay click handler**: Click background to close
- **showMsg()**: Display messages, auto-clear success after 3s

#### JavaScript: Data Fetchers
```javascript
async function fetchDepts() {
    const r = await fetch("/api/departments");
    const d = await r.json();
    return d.ok ? d.departments : [];
}
async function fetchInstructors() {
    const r = await fetch("/api/instructors");
    const d = await r.json();
    return d.ok ? d.instructors : [];
}
async function fetchSubjects() {
    const r = await fetch("/api/subjects");
    const d = await r.json();
    return d.ok ? d.subjects : [];
}
async function fetchAssignments() {
    const r = await fetch("/api/teaches");
    const d = await r.json();
    return d.ok ? d.assignments : [];
}
```
- **Generic async fetchers**: Reusable data loading
- **Error handling**: Returns empty array on failure

#### JavaScript: Select Population
```javascript
function populateSelect(selId, items, valKey, labelFn, placeholder = "— select —") {
    const sel = document.getElementById(selId);
    sel.innerHTML = `<option value="">${placeholder}</option>` +
        items.map(i => `<option value="${i[valKey]}">${labelFn(i)}</option>`).join("");
}
```
- **Generic function**: Populates any select dropdown
- **valKey**: Which property is the value
- **labelFn**: Function to create label text
- **Placeholder**: Default empty option

#### JavaScript: Load Instructors Panel
```javascript
document.getElementById("card-instructors").addEventListener("click", async () => {
    openPanel("panel-instructors");
    await loadInstructorsPanel();
});

async function loadInstructorsPanel() {
    const body = document.getElementById("instructors-body");
    body.innerHTML = '<p class="loading-msg">Loading...</p>';

    const [instructors, depts] = await Promise.all([fetchInstructors(), fetchDepts()]);

    // populate dept dropdown
    populateSelect("i-dept", depts, "Dept_ID", d => `${d.Dept_ID} – ${d.Dept_Name}`);

    if (!instructors.length) {
        body.innerHTML = '<p class="empty-msg">No instructors yet.</p>';
        return;
    }

    body.innerHTML = `
        <table class="data-table">
            <thead><tr>
                <th>ID</th><th>Name</th><th>Department</th><th>Qualification</th><th>Hired</th><th></th>
            </tr></thead>
            <tbody>
                ${instructors.map(i => `
                    <tr>
                        <td>${i.Emp_ID}</td>
                        <td>${i.Emp_FName} ${i.Emp_Lname}</td>
                        <td>${i.Dept_Name}</td>
                        <td>${i.Qualification || '—'}</td>
                        <td>${i.Employment_Date || '—'}</td>
                        <td>
                            <button class="btn-danger" onclick="deleteInstructor(${i.Emp_ID})">Delete</button>
                        </td>
                    </tr>`).join("")}
            </tbody>
        </table>`;
}
```
- **Click handler**: Opens panel and loads data
- **Promise.all()**: Fetch instructors and departments in parallel
- **Populates dropdown**: For add form
- **Renders table**: Lists all instructors with delete buttons
- **Empty state**: Message if no instructors

#### JavaScript: Add Instructor
```javascript
document.getElementById("btn-add-instructor").addEventListener("click", async () => {
    const emp_id = document.getElementById("i-id").value.trim();
    const fname  = document.getElementById("i-fname").value.trim();
    const lname  = document.getElementById("i-lname").value.trim();
    const dept   = document.getElementById("i-dept").value;
    const qual   = document.getElementById("i-qual").value.trim();

    if (!emp_id || !fname || !lname || !dept) {
        showMsg("msg-instructors", "ID, name, and department are required."); return;
    }

    const res  = await fetch("/api/instructors", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ emp_id: +emp_id, fname, lname, dept_id: +dept, qualification: qual || null })
    });
    const data = await res.json();
    if (!data.ok) { showMsg("msg-instructors", data.error || "Failed to add instructor."); return; }

    showMsg("msg-instructors", "Instructor added!", "success");
    ["i-id","i-fname","i-lname","i-qual"].forEach(id => document.getElementById(id).value = "");
    await loadInstructorsPanel();
});
```
- **Gets form values**: From input fields
- **Validates required**: ID, names, department
- **Fetches /api/instructors**: POST request with data
- **Handles errors**: Shows error message
- **Clears form**: On success
- **Reloads panel**: Updates table

#### JavaScript: Delete Instructor
```javascript
async function deleteInstructor(id) {
    if (!confirm(`Delete instructor #${id}? This also removes their course assignments.`)) return;
    const res  = await fetch(`/api/instructors/${id}`, { method: "DELETE" });
    const data = await res.json();
    if (!data.ok) { showMsg("msg-instructors", data.error || "Delete failed."); return; }
    showMsg("msg-instructors", "Instructor deleted.", "success");
    await loadInstructorsPanel();
}
window.deleteInstructor = deleteInstructor;
```
- **Confirmation dialog**: Asks user to confirm
- **Fetches DELETE**: Removes instructor
- **Handles errors**: Shows error
- **Reloads panel**: Updates table
- **Global export**: Makes function callable from HTML

#### JavaScript: Admins Panel
```javascript
document.getElementById("card-admins").addEventListener("click", async () => {
    openPanel("panel-admins");
    const body = document.getElementById("admins-body");
    body.innerHTML = '<p class="loading-msg">Loading...</p>';

    const res  = await fetch("/api/users/admins");
    const data = await res.json();

    if (!data.ok || !data.admins.length) {
        body.innerHTML = '<p class="empty-msg">No admin accounts found.</p>';
        return;
    }

    body.innerHTML = `
        <table class="data-table">
            <thead><tr><th>ID</th><th>Full Name</th><th>Email</th><th>Created</th></tr></thead>
            <tbody>
                ${data.admins.map(a => `
                    <tr>
                        <td>${a.User_ID}</td>
                        <td>${a.Full_Name}</td>
                        <td>${a.Email}</td>
                        <td>${a.Created_At || '—'}</td>
                    </tr>`).join("")}
            </tbody>
        </table>`;
});
```
- **Simpler panel**: Fetch and display only
- **No add/delete**: Read-only view
- **Shows creation time**: Account metadata

#### JavaScript: Course Assignments Panel
```javascript
document.getElementById("card-courses").addEventListener("click", async () => {
    openPanel("panel-courses");
    await loadAssignmentsPanel();
});

async function loadAssignmentsPanel() {
    const [instructors, subjects, assignments] = await Promise.all([
        fetchInstructors(), fetchSubjects(), fetchAssignments()
    ]);

    populateSelect("ca-instructor", instructors, "Emp_ID",
        i => `#${i.Emp_ID} – ${i.Emp_FName} ${i.Emp_Lname}`);
    populateSelect("ca-subject", subjects, "Subject_ID",
        s => `#${s.Subject_ID} – ${s.Subject_Name}`);

    const body = document.getElementById("assignments-body");
    if (!assignments.length) {
        body.innerHTML = '<p class="empty-msg">No assignments yet.</p>';
        return;
    }

    // group by instructor
    const grouped = {};
    assignments.forEach(a => {
        const key = a.Emp_ID;
        if (!grouped[key]) grouped[key] = { name: a.Instructor_Name, courses: [] };
        grouped[key].courses.push(a);
    });

    body.innerHTML = `
        <table class="data-table">
            <thead><tr><th>Instructor</th><th>Assigned Courses</th></tr></thead>
            <tbody>
                ${Object.entries(grouped).map(([empId, g]) => `
                    <tr>
                        <td><strong>${g.name}</strong><br><small style="color:#999">#${empId}</small></td>
                        <td>${g.courses.map(c => `
                            <span class="chip">
                                ${c.Subject_Name}
                                <button onclick="unassignCourse(${empId},${c.Subject_ID})" title="Remove">✕</button>
                            </span>`).join("")}
                        </td>
                    </tr>`).join("")}
            </tbody>
        </table>`;
}
```
- **Fetches all data**: Instructors, subjects, assignments
- **Populates dropdowns**: For assignment form
- **Groups by instructor**: Organizes assignments
- **Shows chips**: Each assignment as removable chip

---

## Styling

### File: `style.css` - Global and Component Styles

#### Global Reset
```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-family: Arial, sans-serif;
}
```
- **Universal selector**: Applies to all elements
- **Removes defaults**: margin and padding
- **box-sizing**: Includes padding in width calculations
- **font-family**: Consistent typography

#### Body and Layout
```css
body {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background: #f5f7fb;
}

.page-wrapper {
    width: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
}
```
- **Flexbox layout**: Vertical centering
- **Full height**: min-height: 100vh
- **Light background**: Subtle color
- **Wrapper**: Centers content horizontally

#### Card Styling
```css
.login-card {
    background: white;
    padding: 40px;
    width: 400px;
    border-radius: 15px;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
    text-align: center;
}

.login-card h2 {
    font-size: 22px;
    margin-bottom: 15px;
    color: #333;
}

.login-card p {
    margin-bottom: 20px;
    color: #666;
}
```
- **Card container**: White background with shadow
- **Rounded corners**: 15px border-radius
- **Fixed width**: 400px
- **Titles**: Larger, dark gray
- **Paragraph text**: Medium gray

#### Input Groups
```css
.input-group {
    text-align: left;
    margin-bottom: 15px;
}

.input-group label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
    color: #444;
}

.input-group input {
    width: 100%;
    padding: 10px;
    border: 1px solid #ccc;
    border-radius: 8px;
    outline: none;
}

.input-group input:focus {
    border-color: #111413;
}
```
- **Label styling**: Bold, gray, block display
- **Input styling**: Full width, subtle border
- **Focus state**: Dark border on focus
- **Padding**: 10px for comfortable interaction

#### Form Messages
```css
.form-message {
    min-height: 22px;
    margin-bottom: 14px;
    color: #b42318;
    font-size: 14px;
    font-weight: bold;
    line-height: 1.35;
}

.form-message.success {
    color: #067647;
}

.form-message:empty {
    margin-bottom: 0;
}
```
- **Error red**: Default color
- **Success green**: Class variant
- **Reserved height**: Prevents layout shift
- **Empty state**: No margin when empty

#### Buttons
```css
.login-btn,
.register-btn {
    display: inline-block;
    width: 100%;
    padding: 12px;
    margin-top: 10px;
    border: none;
    border-radius: 8px;
    background: #111413;
    color: white;
    font-size: 16px;
    text-decoration: none;
    cursor: pointer;
    transition: 0.3s ease;
}
```
- **Full width**: Spans container
- **Dark background**: Professional look
- **Rounded corners**: Soft appearance
- **Smooth transition**: Hover effects

#### Role Selection Buttons
```css
.role-btn {
    flex: 1;
    padding: 14px 20px;
    border: none;
    border-radius: 12px;
    background: #eef2f7;
    color: #111413;
    font-size: 15px;
    font-weight: bold;
    cursor: pointer;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.08);
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}

.role-btn:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 18px rgba(116, 235, 213, 0.35);
    background: linear-gradient(135deg, #74ebd5, #9face6);
    color: white;
}

.role-btn.active {
    background: #111413;    
    color: #fffdfd;
    box-shadow: 0 8px 20px rgba(116, 235, 213, 0.4);
    transform: scale(1.05);
}

.role-btn::before {
    content: "";
    position: absolute;
    top: 0;
    left: -75%;
    width: 50%;
    height: 100%;
    background: rgba(255, 255, 255, 0.3);
    transform: skewX(-25deg);
    transition: 0.5s;
}

.role-btn:hover::before {
    left: 125%;
}
```
- **Three states**: Default, hover, active
- **Hover effects**: Scale up, color gradient
- **Active state**: Dark background, scaled
- **Shine effect**: ::before pseudo-element animation
- **Flex layout**: Equal width buttons

#### Responsive Design
```css
@media (max-width: 768px) {
    .role-buttons {
        flex-direction: column;
    }
}
```
- **Mobile breakpoint**: 768px
- **Stack buttons**: Vertically on mobile

#### Data Tables
```css
.data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
}
.data-table th {
    background: #111413;
    color: #fff;
    padding: 10px 12px;
    text-align: left;
}
.data-table td {
    padding: 10px 12px;
    border-bottom: 1px solid #eee;
    color: #333;
}
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover td { background: #f5f7fb; }
```
- **Header**: Dark background, white text
- **Cells**: Consistent padding, light borders
- **Hover**: Subtle background color
- **Clean look**: Minimal styling

#### Grade Badges
```css
.grade-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-weight: bold;
    font-size: 13px;
}
.grade-a  { background: #d1fae5; color: #065f46; }
.grade-b  { background: #dbeafe; color: #1e40af; }
.grade-c  { background: #fef9c3; color: #854d0e; }
.grade-d  { background: #ffedd5; color: #9a3412; }
.grade-f  { background: #fee2e2; color: #991b1b; }
.grade-na { background: #f3f4f6; color: #6b7280; }
```
- **Color-coded**: Each grade has distinct colors
- **Subtle pastels**: Easy on the eyes
- **Pill shape**: rounded border-radius
- **Semantic colors**: Green (good) to red (poor)

#### Panel Overlays
```css
.panel-overlay {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.45);
    z-index: 100;
    justify-content: center;
    align-items: flex-start;
    padding: 40px 16px;
    overflow-y: auto;
}
.panel-overlay.open { display: flex; }

.panel {
    background: #fff;
    border-radius: 14px;
    width: min(640px, 100%);
    padding: 32px;
    position: relative;
    box-shadow: 0 12px 40px rgba(0,0,0,0.2);
}
```
- **Modal overlay**: Semi-transparent background
- **Responsive width**: max 640px or 100% on mobile
- **Centered**: Flexbox centering
- **Shadow**: Depth perception

#### Close Buttons
```css
.close-btn {
    position: absolute;
    top: 16px; right: 20px;
    background: none;
    border: none;
    font-size: 22px;
    cursor: pointer;
    color: #555;
}
.close-btn:hover { color: #111; }
```
- **Corner positioning**: Top right
- **Simple**: X character, no background
- **Hover**: Darker color

#### Dashboard Cards
```css
.dashboard-card {
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
}
.dashboard-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 30px rgba(0,0,0,0.15);
}
.dashboard-card .card-hint {
    font-size: 12px; color: #9ca3af; margin-top: 10px;
}
```
- **Interactive**: Cursor pointer
- **Hover effect**: Lift and shadow
- **Hint text**: Subtle gray
- **Smooth animation**: 0.2s transitions

---

## Dependencies

### File: `requirements.txt`

```
flask
mysql-connector-python
```

#### Flask
- **Purpose**: Python web framework
- **Used for**: Creating REST API routes, handling requests, sessions
- **Installation**: pip install flask

#### mysql-connector-python
- **Purpose**: MySQL database connector for Python
- **Used for**: Connecting to MySQL, executing queries, retrieving results
- **Installation**: pip install mysql-connector-python

---

## Summary

This School Information System consists of:

1. **Database (db.sql)**: Relational schema with 9 tables managing students, teachers, departments, subjects, classrooms, and relationships
2. **Backend (app.py)**: Flask REST API with 30+ endpoints handling authentication, CRUD operations, and complex queries
3. **Frontend (HTML)**: Four responsive pages (login, signup, dashboards) with JavaScript for interactivity
4. **Styling (CSS)**: Professional UI with hover effects, responsive design, and semantic colors
5. **Dependencies**: Flask and MySQL connector

The system supports three user roles (student, teacher, admin) with role-based dashboards, secure authentication with password hashing, and comprehensive management of academic data.
