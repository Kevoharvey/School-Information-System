# School Information System Code Documentation

This document explains the purpose of each file in the project and describes what each major block of code does. The application is a School Information System called **EduNova**. It uses a Flask backend, a MySQL database, and static HTML/CSS/JavaScript pages.

## Project Structure

```text
School-Information-System/
├── app.py
├── db.sql
├── dbconfiguration.md
├── model.py
├── requirements.txt
├── DOCUMENTATION.md
├── static/
│   ├── index.html
│   ├── student.html
│   ├── teacher.html
│   ├── app.js
│   └── style.css
└── templates/
```

The `templates/` folder currently does not contain active template files. The current frontend is served from the `static/` folder.

## app.py

`app.py` is the Flask backend for the system. It serves the frontend files and exposes JSON API routes that the JavaScript frontend calls with `fetch()`.

### Imports

```python
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
import os

from flask import Flask, jsonify, request, send_from_directory, session
import mysql.connector
from mysql.connector import Error as MySQLError
```

This block imports the tools needed by the backend:

- `Flask`, `jsonify`, `request`, `send_from_directory`, and `session` are used to build routes, return JSON, read request data, serve static files, and remember logged-in users.
- `mysql.connector` connects Flask to the MySQL database.
- `contextmanager` helps safely open and close database connections.
- `date`, `datetime`, and `Decimal` are used to convert database values into JSON-friendly values.
- `os` reads environment variables for configuration.

### Flask App Setup

```python
app = Flask(__name__, static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", "school_is_secret_key_2026")
```

This creates the Flask application and tells Flask that static frontend files live in the `static/` folder. The secret key is used to sign session cookies. It can be loaded from the `SECRET_KEY` environment variable, or it falls back to a default development key.

### Database Configuration

```python
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME", "school_db"),
    "port": int(os.environ.get("DB_PORT", "3306")),
}
```

This block stores the MySQL connection settings. The code supports environment variables, so the database settings can be changed without editing the Python file.

Default values:

- Database host: `localhost`
- Database user: `root`
- Database password: empty string
- Database name: `school_db`
- Database port: `3306`

### Database Connection Helper

```python
def get_db():
    return mysql.connector.connect(**DB_CONFIG)
```

This function opens a new connection to MySQL using `DB_CONFIG`.

### Database Cursor Context Manager

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

This block safely opens a database connection and cursor, then closes both when the query is finished. `dictionary=True` makes rows come back as dictionaries, which are easier to convert into JSON.

### JSON Serialization Helpers

```python
def serialize_value(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value
```

This function converts database values that JSON does not naturally understand:

- Dates become ISO strings like `2026-05-01`.
- Decimal numbers become Python floats.
- Other values are returned as they are.

```python
def serialize_rows(rows):
    if rows is None:
        return None
    if isinstance(rows, dict):
        return {key: serialize_value(value) for key, value in rows.items()}
    return [{key: serialize_value(value) for key, value in row.items()} for row in rows]
```

This function applies `serialize_value()` to a single database row or a list of database rows.

### General Database Query Function

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

This is the main helper used by all API routes.

- `sql` is the SQL command.
- `params` safely passes values into the SQL query.
- `fetchone=True` returns one row.
- `commit=True` saves insert, update, or delete changes.
- Results are converted into JSON-safe values before returning.

### Database Error Handler

```python
@app.errorhandler(MySQLError)
def handle_database_error(error):
    return jsonify({
        "ok": False,
        "error": "Database error",
        "detail": str(error),
    }), 500
```

This catches MySQL errors and returns a JSON response instead of crashing with an HTML error page. The response includes `ok: false`, a general error label, and the database error detail.

### Frontend Routes

```python
@app.route("/")
def index():
    return send_from_directory("static", "index.html")
```

This route serves the homepage from `static/index.html`.

```python
@app.route("/student")
def student_page():
    return send_from_directory("static", "student.html")
```

This route serves the separate student dashboard page.

```python
@app.route("/teacher")
def teacher_page():
    return send_from_directory("static", "teacher.html")
```

This route serves the separate teacher dashboard page.

```python
@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)
```

This route serves static assets such as CSS, JavaScript, and images from the `static/` folder.

### Health Check Route

```python
@app.route("/api/health")
def api_health():
    db_query("SELECT 1 AS ok", fetchone=True)
    return jsonify({"ok": True})
```

This route checks whether Flask can successfully talk to the database. If the query works, it returns `{"ok": true}`.

### Authentication Routes

```python
@app.route("/api/signin", methods=["POST"])
def api_signin():
```

This route logs in either a student or a teacher.

Main steps:

- Reads JSON sent by the frontend.
- Checks that the selected role is `student` or `teacher`.
- Checks that the ID is numeric.
- For students, looks up the user in the `Student` table.
- For teachers, looks up the user by joining `Employee` and `Instructor`.
- Stores the logged-in user in the Flask session.
- Returns the logged-in user as JSON.

Current supported roles are only `student` and `teacher`.

```python
@app.route("/api/signup", methods=["POST"])
def api_signup():
```

This route creates a new student or teacher account.

Main steps:

- Reads name, email, ID, password, and role from JSON.
- Validates required fields.
- Splits the full name into first and last name.
- Inserts a student into the `Student` table when the role is `student`.
- Inserts a teacher into both `Employee` and `Instructor` when the role is `teacher`.
- Stores the new user in the session.

Passwords are validated for length, but they are not currently stored or checked against a password table. This is acceptable for a class prototype, but a production system should store hashed passwords.

```python
@app.route("/api/signout", methods=["POST"])
def api_signout():
```

This route clears the Flask session, which logs the user out.

```python
@app.route("/api/me")
def api_me():
```

This route returns the currently logged-in user from the session. If no user is logged in, it returns `ok: false` with a `401` status.

### Dashboard Stats Route

```python
@app.route("/api/stats")
def api_stats():
```

This route counts records in the main database tables:

- `Student`
- `Instructor`
- `Subject`
- `Department`
- `Classroom`

It also returns the five most recent students. The homepage and dashboards use this route to show live numbers.

### Student API Routes

```python
@app.route("/api/students", methods=["GET"])
def api_students_list():
```

Returns all students ordered by `Student_ID`.

```python
@app.route("/api/students", methods=["POST"])
def api_students_add():
```

Adds a new student to the `Student` table.

```python
@app.route("/api/students/<int:student_id>", methods=["PUT"])
def api_students_edit(student_id):
```

Updates an existing student's name, level, email, address, and birth date.

```python
@app.route("/api/students/<int:student_id>", methods=["DELETE"])
def api_students_delete(student_id):
```

Deletes a student by ID.

```python
@app.route("/api/students/<int:student_id>/grades")
def api_student_grades(student_id):
```

Returns a student's grades by joining:

- `Studies`
- `Subject`

This lets the frontend display grades with subject names.

### Grade Route

```python
@app.route("/api/grades", methods=["POST"])
def api_grades_upsert():
```

This route inserts or updates a grade in the `Studies` table.

It uses:

```sql
ON DUPLICATE KEY UPDATE
```

That means:

- If the student-subject pair does not exist, it creates it.
- If the student-subject pair already exists, it updates the grade.

The route also checks that grades are between `0` and `100`.

### Instructor API Routes

```python
@app.route("/api/instructors", methods=["GET"])
def api_instructors_list():
```

Returns instructors by joining:

- `Instructor`
- `Employee`
- `Department`

This gives the frontend teacher names, qualifications, departments, and employment dates.

```python
@app.route("/api/instructors", methods=["POST"])
def api_instructors_add():
```

Adds a new instructor by first inserting the employee record, then inserting the instructor record.

```python
@app.route("/api/instructors/<int:emp_id>", methods=["DELETE"])
def api_instructors_delete(emp_id):
```

Deletes an instructor by deleting the employee row. Because `Instructor.Emp_ID` has `ON DELETE CASCADE`, the related instructor row is deleted automatically.

### Employee API Routes

```python
@app.route("/api/employees", methods=["GET"])
def api_employees_list():
```

Returns all employees, including department names and supervisor names.

```python
@app.route("/api/employees", methods=["POST"])
def api_employees_add():
```

Adds a new employee.

```python
@app.route("/api/employees/<int:emp_id>", methods=["DELETE"])
def api_employees_delete(emp_id):
```

Deletes an employee by employee ID.

### Subject API Routes

```python
@app.route("/api/subjects", methods=["GET"])
def api_subjects_list():
```

Returns all subjects and their classroom building/floor information.

```python
@app.route("/api/subjects", methods=["POST"])
def api_subjects_add():
```

Adds a subject with optional level, slot count, and classroom.

```python
@app.route("/api/subjects/<int:subject_id>", methods=["DELETE"])
def api_subjects_delete(subject_id):
```

Deletes a subject by ID.

### Classroom API Routes

```python
@app.route("/api/classrooms", methods=["GET"])
def api_classrooms_list():
```

Returns all classrooms.

```python
@app.route("/api/classrooms", methods=["POST"])
def api_classrooms_add():
```

Adds a classroom with level, capacity, building, and floor.

```python
@app.route("/api/classrooms/<int:classroom_id>", methods=["DELETE"])
def api_classrooms_delete(classroom_id):
```

Deletes a classroom by ID.

### Department API Routes

```python
@app.route("/api/departments", methods=["GET"])
def api_departments_list():
```

Returns all departments.

```python
@app.route("/api/departments", methods=["POST"])
def api_departments_add():
```

Adds a new department.

```python
@app.route("/api/departments/<int:dept_id>", methods=["DELETE"])
def api_departments_delete(dept_id):
```

Deletes a department by ID.

### Teacher-Specific Routes

```python
@app.route("/api/teacher/<int:emp_id>/subjects")
def api_teacher_subjects(emp_id):
```

Returns the subjects taught by one teacher by joining `Teaches` and `Subject`.

```python
@app.route("/api/teacher/<int:emp_id>/students")
def api_teacher_students(emp_id):
```

Returns students enrolled in subjects taught by a teacher. It joins:

- `Studies`
- `Student`
- `Teaches`

### Run Block

```python
if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
```

This starts the Flask development server when running:

```bash
python3 app.py
```

The app runs on:

```text
http://127.0.0.1:5000
```

## db.sql

`db.sql` defines the MySQL database schema for the School Information System.

### Database Creation

```sql
CREATE DATABASE IF NOT EXISTS school_db;
USE school_db;
```

This creates the database if it does not already exist, then selects it for the rest of the SQL commands.

### Department Table

```sql
CREATE TABLE Department (
    Dept_ID INT PRIMARY KEY,
    Dept_Name VARCHAR(100) NOT NULL,
    Dept_Head VARCHAR(100)
);
```

Stores school departments.

- `Dept_ID` uniquely identifies each department.
- `Dept_Name` stores the department name.
- `Dept_Head` stores the name of the head of department.

### Employee Table

```sql
CREATE TABLE Employee (...)
```

Stores employees who work at the school.

Important fields:

- `Emp_ID`: primary key.
- `Emp_FName`, `Emp_Lname`: employee name split into first and last name.
- `Employment_Date`: date the employee started.
- `Supervisor_ID`: self-referencing foreign key pointing to another employee.
- `Dept_ID`: foreign key connecting employee to department.

This table represents the `Works_At` relationship through `Dept_ID`, and the supervisor relationship through `Supervisor_ID`.

### Employee_Phone Table

```sql
CREATE TABLE Employee_Phone (...)
```

Stores multiple phone numbers for one employee. This avoids putting repeated phone number fields inside the `Employee` table.

The primary key is composite:

```sql
PRIMARY KEY (Emp_ID, Emp_pnum)
```

This means the same phone number cannot be repeated for the same employee.

### Instructor Table

```sql
CREATE TABLE Instructor (...)
```

Represents instructors as a specialized type of employee.

- `Emp_ID` is both the primary key and a foreign key.
- `Qualification` stores the instructor qualification.
- `ON DELETE CASCADE` means if the employee is deleted, the instructor row is also deleted.

### Classroom Table

```sql
CREATE TABLE Classroom (...)
```

Stores classroom information.

Important fields:

- `Classroom_ID`: unique classroom number.
- `Classroom_Level`: classroom level or category.
- `Classroom_Capacity`: number of students the room can hold.
- `Classroom_Building`: building name.
- `Classroom_Floor`: floor number/name.

### Subject Table

```sql
CREATE TABLE Subject (...)
```

Stores school subjects.

Important fields:

- `Subject_ID`: unique subject ID.
- `Subject_Name`: subject name.
- `Subject_Level`: academic level.
- `Subject_Slots`: number of teaching slots.
- `Classroom_ID`: optional foreign key showing where the subject is held.

### Student Table

```sql
CREATE TABLE Student (...)
```

Stores student information.

Important fields:

- `Student_ID`: primary key.
- `Fname`, `Lname`: student first and last name.
- `Level`: academic level.
- `Birth_Date`: used to derive age.
- `Student_Email`: email address.
- `City`, `Street`, `Building_Num`: address components.

### Studies Table

```sql
CREATE TABLE Studies (...)
```

This is a junction table between students and subjects.

It represents:

- A student can study many subjects.
- A subject can have many students.

The `Grades` column belongs here because a grade only makes sense for a specific student in a specific subject.

### Teaches Table

```sql
CREATE TABLE Teaches (...)
```

This is a junction table between instructors and subjects.

It represents:

- A teacher can teach many subjects.
- A subject can be taught by many teachers.

## dbconfiguration.md

`dbconfiguration.md` is an explanatory document for the database design. It describes relational database concepts and explains the schema in a more academic style.

### Overview Section

Explains the purpose of the database and the type of school/university data it manages.

### Relational Database Concepts Section

Explains database ideas such as:

- Primary keys.
- Foreign keys.
- Cascade behavior.
- Setting foreign keys to `NULL`.

Some of this file describes an earlier or more general database design. For example, it mentions tables like `Student_Email`, `Instructor_Qualification`, and `Is_In`, but the current `db.sql` file does not include those exact tables. The current active schema is the one in `db.sql`.

### Entity Breakdown Section

Explains the purpose of tables such as:

- `Department`
- `Employee`
- `Instructor`
- `Student`
- `Subject`
- `Classroom`

### Junction Tables Section

Explains many-to-many relationship tables such as:

- `Teaches`
- `Studies`

The explanation is useful for understanding the ERD/database theory behind the project.

## model.py

`model.py` is currently empty.

This means the project does not currently define Python classes or ORM models. The backend talks directly to MySQL using raw SQL queries in `app.py`.

Possible future use:

- Define database model classes.
- Move database-related logic out of `app.py`.
- Add an ORM such as SQLAlchemy.

## requirements.txt

```text
flask
mysql-connector-python
```

This file lists Python packages needed to run the project.

- `flask`: web framework used for routes, sessions, static file serving, and JSON APIs.
- `mysql-connector-python`: MySQL driver used to connect Python to the MySQL database.

Install dependencies with:

```bash
pip install -r requirements.txt
```

## static/index.html

`index.html` is the main public-facing page. It contains the homepage, public information pages, sign-in form, and sign-up form.

### Head Block

The `<head>` block sets:

- Character encoding.
- Responsive viewport behavior.
- Browser title.
- Google Fonts.
- Link to `/static/style.css`.

### Navbar Block

The navbar contains:

- EduNova logo.
- Guest navigation links: Home, Teachers, Subjects, Classrooms.
- Sign In button.
- Browse as Guest button.

The navbar uses `onclick` handlers like:

```html
onclick="showPage('home')"
```

These call functions from `static/app.js`.

### Toast Block

```html
<div id="toast"></div>
```

This is an empty notification container. JavaScript fills it with messages when something happens, such as login errors or logout messages.

### Home Page Block

```html
<div class="page active" id="page-home">
```

This is the default visible page. It includes:

- Hero section.
- Main heading and school introduction.
- Call-to-action buttons.
- Live stats bar.
- Feature cards.
- About school information.
- Contact and accreditation facts.

### Public Teachers Page

```html
<div class="page" id="page-teachers">
```

This page displays teacher cards. The container:

```html
<div class="teacher-grid" id="public-teachers-grid">
```

is filled dynamically by `loadPublicTeachers()` in `app.js`.

### Public Subjects Page

```html
<div class="page" id="page-subjects">
```

This page displays subjects in a table. The table body:

```html
<tbody id="public-subjects-tbody">
```

is filled dynamically by `loadPublicSubjects()`.

### Public Classrooms Page

```html
<div class="page" id="page-classrooms">
```

This page displays classrooms. The list:

```html
<div class="room-list" id="public-classrooms-list">
```

is filled dynamically by `loadPublicClassrooms()`.

### Sign In Page

```html
<div class="page" id="page-signin">
```

This page contains:

- Role picker for student/teacher.
- Numeric ID input.
- Password input.
- Sign In button.
- Link to the sign-up page.

Note: The current HTML uses `id="signin-id"`, while `app.js` currently reads from `signin-email`. That mismatch should be fixed for the login form to work correctly.

### Sign Up Page

```html
<div class="page" id="page-signup">
```

This page contains:

- Role picker for student/teacher.
- Full name input.
- Email input.
- Student/staff ID input.
- Password input.
- Create Account button.

### Script Block

```html
<script src="/static/app.js"></script>
```

Loads the main frontend JavaScript.

The inline `loadHomeStats()` function calls `/api/stats` and updates the stats bar on the homepage.

## static/app.js

`app.js` controls page navigation, authentication, and dynamic data loading for the static frontend.

### Global State

```javascript
var currentUser = null;
var selectedRole = 'student';
var signupRole = 'student';
```

These variables track:

- The currently logged-in user.
- The selected login role.
- The selected sign-up role.

### Helper Functions

```javascript
function showToast(message)
```

Displays a temporary notification message inside the `#toast` element.

```javascript
async function api(method, url, body)
```

Wraps `fetch()` so the rest of the code can call Flask API routes more easily. It sends JSON and returns parsed JSON.

### Page Navigation

```javascript
function showPage(pageId)
```

Shows one public page and hides the others. It also loads dynamic data when the selected page needs it.

```javascript
function showStudentPage(subId)
```

Shows a student dashboard sub-page and loads student-specific data when needed.

```javascript
function showTeacherPage(subId)
```

Shows a teacher dashboard sub-page and loads teacher-specific data when needed.

```javascript
function showDashboard(role)
```

Shows either the student dashboard or teacher dashboard container.

### Role Pickers

```javascript
function selectRole(role)
```

Changes the selected role on the sign-in form.

```javascript
function selectSignupRole(role)
```

Changes the selected role on the sign-up form and updates the ID label to say either Student ID or Staff ID.

### Sign In

```javascript
async function doSignIn()
```

Reads login input, validates it, sends it to `/api/signin`, and calls `loginUser()` if login succeeds.

Important note: this function currently looks for `signin-email`, but `index.html` contains `signin-id`. The IDs should match.

### Sign Up

```javascript
async function doSignUp()
```

Reads sign-up inputs, validates them, sends them to `/api/signup`, and logs the user in if account creation succeeds.

### Login UI Update

```javascript
function loginUser(user)
```

Stores the user in `currentUser`, updates the navbar, builds the user badge, and shows either the student or teacher dashboard.

### Logout

```javascript
async function logout()
```

Calls `/api/signout`, clears local user state, resets the navbar, and returns to the homepage.

### Student Dashboard Data

```javascript
async function loadStudentDashboard()
```

Calls `/api/stats` and updates dashboard stat cards.

```javascript
async function loadStudentGrades()
```

Calls `/api/students/<id>/grades` and fills the grades table.

```javascript
function gradeClass(score)
function gradeLabel(score)
```

Convert numeric grades into visual classes and letter labels.

### Teacher Dashboard Data

```javascript
async function loadTeacherDashboard()
```

Calls `/api/teacher/<id>/subjects` and displays subjects assigned to the teacher.

```javascript
async function loadTeacherStudents()
```

Calls `/api/teacher/<id>/students` and fills the teacher's student table.

### Public Data Pages

```javascript
async function loadPublicTeachers()
```

Calls `/api/instructors` and builds teacher cards.

```javascript
async function loadPublicSubjects()
```

Calls `/api/subjects` and fills the public subject table.

```javascript
async function loadPublicClassrooms()
```

Calls `/api/classrooms` and builds classroom cards.

### Classroom Booking UI

```javascript
async function loadTeacherClassrooms()
```

Calls `/api/classrooms` and displays available classrooms for the teacher.

```javascript
function bookClassroom(roomId)
function cancelBooking(roomId)
```

Currently show toast messages only. They do not save bookings to the database yet.

### Initialization

```javascript
document.addEventListener('DOMContentLoaded', async function () {
```

When the page loads, the app calls `/api/me` to check if a user is already logged in. If a session exists, it restores the dashboard. If not, it shows the homepage.

## static/student.html

`student.html` is a separate student dashboard page. It is currently served by `/student`.

### Head Block

Loads the page title, Google Fonts, and `style.css`.

### Navbar Block

Contains dashboard navigation links:

- Dashboard
- My Grades
- Quizzes
- Assignments
- Schedule
- Attendance

It also contains the logged-in student badge and logout icon.

### Sidebar Block

The sidebar provides the same student navigation links in a vertical layout, plus public info links.

### Dashboard Sub-Page

```html
<div class="sub-page active" id="stu-dashboard">
```

Shows:

- Greeting.
- School metrics.
- Announcements.
- Today's schedule.

Some values are static, while stat cards are intended to be filled dynamically.

### My Grades Sub-Page

```html
<div class="sub-page" id="stu-grades">
```

Contains a grades table. The table body has `id="grades-tbody"` so JavaScript can insert rows from the database.

### Quizzes Sub-Page

Displays static quiz examples, including graded and upcoming quizzes.

### Assignments Sub-Page

Displays static assignment examples with status pills such as Submitted, Pending, and Late.

### Schedule Sub-Page

Displays a weekly timetable as a static table.

### Attendance Sub-Page

Displays static attendance totals and attendance-by-subject rows.

### Script Reference

```html
<script src="/static/student.js"></script>
```

This file is referenced, but `static/student.js` is not currently present in the project. Student dashboard behavior is currently mostly implemented in `static/app.js`.

## static/teacher.html

`teacher.html` is a separate teacher dashboard page. It is currently served by `/teacher`.

### Head Block

Loads the page title, Google Fonts, and `style.css`.

### Navbar Block

Contains teacher navigation links:

- Dashboard
- Enter Grades
- Upload Quiz
- Assignments
- My Students
- Attendance
- Classroom Booking

It also contains the teacher badge and logout icon.

### Sidebar Block

Provides the same teacher navigation links in a vertical layout.

### Dashboard Sub-Page

```html
<div class="sub-page active" id="tch-dashboard">
```

Shows:

- Teacher greeting.
- My Subjects area.
- Today's classes.

The `tch-subjects-list` container is intended to be filled dynamically.

### Enter Grades Sub-Page

```html
<div class="sub-page" id="tch-grades">
```

Contains inputs for:

- Student ID.
- Subject ID.
- Grade.

The Save Grade button calls:

```html
onclick="saveGrade()"
```

However, `saveGrade()` is not currently defined in the available JavaScript files.

### Upload Quiz Sub-Page

Contains static form controls for creating a quiz. The upload behavior currently only shows toast messages and does not send quiz data to the backend.

### Assignments Sub-Page

Contains static form controls and a static assignments table.

### My Students Sub-Page

Contains a table body with:

```html
id="tch-students-tbody"
```

This is designed to be filled dynamically from `/api/teacher/<id>/students`.

### Attendance Sub-Page

Displays static attendance radio buttons for a sample class.

### Classroom Booking Sub-Page

Contains:

- A dynamic classroom grid with `id="tch-classroom-grid"`.
- A static booking example.

The frontend can load classrooms from `/api/classrooms`.

### Script Reference

```html
<script src="/static/teacher.js"></script>
```

This file is referenced, but `static/teacher.js` is not currently present in the project. Teacher dashboard behavior is currently mostly implemented in `static/app.js`.

## static/style.css

`style.css` contains all visual styling for the public pages and dashboards.

### Root Variables

```css
:root { ... }
```

Defines shared design tokens:

- Colors such as navy, gold, blue, green, red, purple.
- Background colors.
- Border color.
- Shadow values.

These variables make it easier to keep the design consistent.

### Reset and Body

The reset removes default spacing and sets `box-sizing: border-box`. The `body` rule sets the default font, background color, text color, and minimum page height.

### Navbar

Styles:

- Fixed top navigation.
- Logo.
- Navigation links.
- Active/hover states.
- Right-side action buttons.

### Buttons

Defines reusable button classes:

- `.btn`
- `.btn-ghost`
- `.btn-ghost-white`
- `.btn-gold`
- `.btn-primary`
- `.btn-outline`
- `.btn-danger`
- `.btn-success`

Each class controls color, hover behavior, and spacing.

### User Badge

Styles the logged-in user badge, avatar circle, role-specific colors, username, and logout icon.

### Toast Notification

Styles the floating notification box shown by `showToast()` in JavaScript.

### Page System

```css
.page { display: none; }
.page.active { display: block; }
.sub-page { display: none; }
.sub-page.active { display: block; }
```

This is how the JavaScript shows one page or sub-page at a time.

### Home Hero

Styles the homepage hero section, including:

- Full-width hero area.
- Background image overlay.
- Large headline.
- Tag label.
- Hero buttons.

### Stats Bar

Styles the horizontal statistics bar that shows counts for students, teachers, classrooms, and subjects.

### Shared Sections

Defines reusable section spacing, section labels, titles, and subtitles.

### Feature Cards

Styles the cards on the homepage that explain features like grade tracking, quizzes, assignments, schedules, attendance, and announcements.

### Info Section

Styles the dark school information section with text on one side and fact cards on the other.

### Auth Pages

Styles sign-in and sign-up pages:

- Centered auth box.
- EduNova logo.
- Role picker.
- Inputs.
- Submit button.
- Switch links.
- Divider.

### Dashboard Layout

Styles the logged-in dashboard structure:

- `.dash-layout`: overall layout.
- `.sidebar`: left navigation.
- `.dash-main`: main content area.
- `.dash-header`: dashboard page headings.

### Metric Cards

Styles dashboard stat cards and colored badges.

### Content Cards

Styles reusable dashboard cards used for tables, lists, announcements, schedules, and forms.

### Tables

Styles table headers, table cells, hover behavior, and horizontal overflow wrappers.

### Pills and Badges

Styles grade pills and status pills:

- Grade A/B/C/D/F colors.
- Done, pending, late, and upcoming statuses.

### Item Lists

Styles rows used in quiz and assignment lists.

### Progress Bar

Provides styles for progress bar containers and fills, although this pattern is not heavily used in the current pages.

### Announcements

Styles announcement rows with colored dots, titles, text, and dates.

### Schedule

Styles schedule rows with times, colored dots, class names, and rooms.

### Upload Area

Styles the dashed upload area used in the teacher quiz page.

### Public Pages

Styles public Teachers, Subjects, and Classrooms pages:

- `.pub-page`
- `.teacher-grid`
- `.teacher-card`
- `.room-list`
- `.room-card`

### Responsive Rules

The media queries adjust layout for tablets and phones:

- Reduce hero text size.
- Stack dashboard layout.
- Make navigation/sidebar more compact.
- Adjust grids to fit smaller screens.

### Classroom Booking

Styles classroom booking cards and booking list items:

- Available/booked classroom states.
- Classroom capacity/status labels.
- Booking room, time, and purpose.

## static/index.html, static/student.html, and static/teacher.html Relationship

There are two dashboard approaches in the project:

1. `index.html` contains embedded dashboard page containers expected by `app.js`, such as `page-student` and `page-teacher`.
2. `student.html` and `teacher.html` are separate dashboard pages served by Flask routes `/student` and `/teacher`.

The current `app.js` mainly expects dashboard containers inside `index.html`, while the separate dashboard pages reference missing files `student.js` and `teacher.js`. This means the project has a partial transition between a single-page app layout and separate dashboard pages.

## Current API Summary

| Route | Method | Purpose |
|---|---:|---|
| `/` | GET | Serve homepage |
| `/student` | GET | Serve student dashboard page |
| `/teacher` | GET | Serve teacher dashboard page |
| `/api/health` | GET | Check database connection |
| `/api/signin` | POST | Sign in student or teacher |
| `/api/signup` | POST | Create student or teacher account |
| `/api/signout` | POST | Log out current user |
| `/api/me` | GET | Get current session user |
| `/api/stats` | GET | Get dashboard counts |
| `/api/students` | GET | List students |
| `/api/students` | POST | Add student |
| `/api/students/<id>` | PUT | Edit student |
| `/api/students/<id>` | DELETE | Delete student |
| `/api/students/<id>/grades` | GET | Get student grades |
| `/api/grades` | POST | Add or update grade |
| `/api/instructors` | GET | List instructors |
| `/api/instructors` | POST | Add instructor |
| `/api/instructors/<id>` | DELETE | Delete instructor |
| `/api/employees` | GET | List employees |
| `/api/employees` | POST | Add employee |
| `/api/employees/<id>` | DELETE | Delete employee |
| `/api/subjects` | GET | List subjects |
| `/api/subjects` | POST | Add subject |
| `/api/subjects/<id>` | DELETE | Delete subject |
| `/api/classrooms` | GET | List classrooms |
| `/api/classrooms` | POST | Add classroom |
| `/api/classrooms/<id>` | DELETE | Delete classroom |
| `/api/departments` | GET | List departments |
| `/api/departments` | POST | Add department |
| `/api/departments/<id>` | DELETE | Delete department |
| `/api/teacher/<id>/subjects` | GET | Get teacher subjects |
| `/api/teacher/<id>/students` | GET | Get teacher students |

## Important Notes

- The backend currently supports `student` and `teacher` roles only.
- There is no completed administration role yet.
- `model.py` is empty.
- `student.html` references `student.js`, but that file is missing.
- `teacher.html` references `teacher.js`, but that file is missing.
- `index.html` login input uses `signin-id`, while `app.js` expects `signin-email`. That should be corrected for the sign-in flow.
- Passwords are not currently stored or verified securely. A production app should use a users table and password hashing.
- The database schema in `db.sql` is the active schema. `dbconfiguration.md` contains useful design explanation but includes references to some tables that are not present in the current SQL file.
