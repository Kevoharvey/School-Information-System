from functools import wraps
import json
import os
import re
import secrets
import smtplib
from uuid import uuid4
from email.message import EmailMessage

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash as werkzeug_check_password_hash

from db_config import execute, query

try:
    from google import genai
except Exception:
    genai = None


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-this-secret-key")
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

bcrypt = Bcrypt(app)
MAILPIT_HOST = os.environ.get("MAILPIT_HOST", "localhost")
MAILPIT_PORT = int(os.environ.get("MAILPIT_PORT", "1025"))
MAIL_FROM = os.environ.get("MAIL_FROM", "noreply@galala.local")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
ai_client = genai.Client(api_key=GEMINI_API_KEY) if genai and GEMINI_API_KEY else None

DB_SCHEMA = """
You are the Galala International School data assistant.
Return only JSON with keys sql and explanation.
Use SELECT statements only. Add LIMIT 50 unless the user asks for a smaller limit.

Tables:
Users(User_ID, Full_Name, Email, Role)
Student(Student_ID, User_ID, Fname, Lname, Level, Batch_Year, Birth_Date, Gender, Nationality, Student_Email, Student_Pnum, Parent_Name, Parent_Pnum, Parent_Email, Student_Address, Previous_School, Student_Photo, Birth_Certificate, Previous_Transcript, Notes, Status, Enrolled_At)
Employee(Emp_ID, User_ID, Emp_FName, Emp_Lname, Emp_Email, Emp_Pnum, Employment_Date, Emp_Status, Dept_ID)
Instructor(Emp_ID, Qualification, Specialization)
Department(Dept_ID, Dept_Name, Dept_Head)
Subject(Subject_ID, Subject_Name, Subject_Level, Credits, Dept_ID, Classroom_ID)
Studies(Student_ID, Subject_ID, Grade, Semester)
Assignment(Assignment_ID, Title, Description, Subject_ID, Emp_ID, Due_Date, Max_Score, File_Path, Status, Created_At)
Submission(Sub_ID, Assignment_ID, Student_ID, File_Path, Notes, Score, Feedback, Submitted_At)
Schedule_Entry(Entry_ID, Subject_ID, Classroom_ID, Emp_ID, Day_Of_Week, Start_Time, End_Time)
Notification(Notif_ID, User_ID, Title, Message, Type, Is_Read, Created_At)
Online_Registration(Reg_ID, Full_Name, Birth_Date, Gender, Nationality, Email, Phone, Grade_Applied, Parent_Name, Parent_Phone, Parent_Email, Address, Previous_School, Birth_Certificate, Student_Photo, Previous_Transcript, Notes, Status, Submitted_At)
"""


def login_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return func(*args, **kwargs)

    return decorated


def admin_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            flash("Admin access required.", "danger")
            return redirect(url_for("dashboard"))
        return func(*args, **kwargs)

    return decorated


def role_required(*roles):
    def wrapper(func):
        @wraps(func)
        def decorated(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            if session.get("role") not in roles:
                flash("You do not have permission to open that page.", "danger")
                return redirect(url_for("dashboard"))
            return func(*args, **kwargs)

        return decorated

    return wrapper


def teacher_or_admin_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        if session.get("role") not in ("teacher", "admin"):
            flash("Teacher access required.", "danger")
            return redirect(url_for("dashboard"))
        return func(*args, **kwargs)

    return decorated


def student_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        if session.get("role") != "student":
            flash("Student access required.", "danger")
            return redirect(url_for("dashboard"))
        return func(*args, **kwargs)

    return decorated


@app.context_processor
def inject_user():
    return {
        "current_user": session.get("email"),
        "user_name": session.get("name"),
        "user_role": session.get("role"),
        "user_id": session.get("user_id"),
        "current_year": 2026,
    }


def count(sql, params=None):
    row = query(sql, params, fetchone=True) or {}
    return row.get("c") or 0


def safe_filename(field_name):
    file = request.files.get(field_name)
    if not file or not file.filename:
        return None
    original = secure_filename(file.filename)
    if not original:
        return None
    filename = f"{uuid4().hex}_{original}"
    file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    return f"uploads/{filename}"


def split_name(full_name):
    parts = (full_name or "").strip().split()
    first = parts[0] if parts else ""
    last = " ".join(parts[1:]) if len(parts) > 1 else first
    return first, last


def ensure_department(name):
    dept_name = (name or "General").strip() or "General"
    row = query("SELECT Dept_ID FROM Department WHERE Dept_Name=%s", (dept_name,), fetchone=True)
    if row:
        return row["Dept_ID"]
    return execute("INSERT INTO Department (Dept_Name) VALUES (%s)", (dept_name,))


def current_student_id():
    if session.get("role") != "student":
        return None
    row = query("SELECT Student_ID FROM Student WHERE User_ID=%s", (session.get("user_id"),), fetchone=True)
    return row["Student_ID"] if row else None


def current_teacher_id():
    if session.get("role") != "teacher":
        return None
    row = query("SELECT Emp_ID FROM Employee WHERE User_ID=%s", (session.get("user_id"),), fetchone=True)
    return row["Emp_ID"] if row else None


def login_user(user):
    session.clear()
    session["user_id"] = user["User_ID"]
    session["email"] = user["Email"]
    session["name"] = user["Full_Name"]
    session["role"] = user["Role"]


def verify_password_and_upgrade_if_needed(user, password):
    stored_hash = user.get("Password_Hash") or ""
    user_id = user.get("User_ID")
    if not stored_hash or not user_id:
        return False
    try:
        return bcrypt.check_password_hash(stored_hash, password)
    except ValueError:
        # Support legacy non-bcrypt hashes and transparently upgrade on success.
        try:
            valid_legacy = werkzeug_check_password_hash(stored_hash, password)
        except ValueError:
            valid_legacy = False
        if valid_legacy:
            new_hash = bcrypt.generate_password_hash(password).decode("utf-8")
            execute("UPDATE Users SET Password_Hash=%s WHERE User_ID=%s", (new_hash, user_id))
            return True
        return False


def generate_temp_password(length=12):
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def send_temporary_credentials_email(recipient_name, recipient_email, role, temp_password):
    message = EmailMessage()
    message["Subject"] = "Welcome to Galala International School"
    message["From"] = MAIL_FROM
    message["To"] = recipient_email
    message.set_content(
        f"""Hello {recipient_name},

Welcome to Galala International School.
Your {role} account was created by the administration team.

Temporary login email: {recipient_email}
Temporary password: {temp_password}

Please log in and change your password as soon as possible.

Best regards,
Galala International School
"""
    )
    html_body = f"""
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Welcome to Galala International School</title>
    <style>
      body {{
        margin: 0;
        padding: 0;
        background: #f4f7fb;
        font-family: Arial, Helvetica, sans-serif;
        color: #1f2937;
      }}
      .wrapper {{
        width: 100%;
        padding: 24px 12px;
      }}
      .card {{
        max-width: 640px;
        margin: 0 auto;
        background: #ffffff;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        overflow: hidden;
      }}
      .header {{
        background: linear-gradient(135deg, #2f64ff, #1f4fd8);
        color: #ffffff;
        padding: 22px 26px;
      }}
      .header h1 {{
        margin: 0;
        font-size: 22px;
      }}
      .content {{
        padding: 24px 26px 12px;
        line-height: 1.6;
        font-size: 15px;
      }}
      .credentials {{
        margin: 16px 0;
        background: #f9fbff;
        border: 1px solid #d8e4ff;
        border-radius: 10px;
        padding: 14px 16px;
      }}
      .credentials p {{
        margin: 6px 0;
      }}
      .label {{
        color: #4b5563;
        font-size: 13px;
      }}
      .value {{
        font-weight: 700;
        color: #111827;
      }}
      .footer {{
        padding: 4px 26px 24px;
        font-size: 13px;
        color: #6b7280;
      }}
    </style>
  </head>
  <body>
    <div class="wrapper">
      <div class="card">
        <div class="header">
          <h1>Welcome to Galala International School</h1>
        </div>
        <div class="content">
          <p>Hello {recipient_name},</p>
          <p>
            We are happy to have you with us. Your <strong>{role}</strong> account has been created by the school administration team.
          </p>
          <div class="credentials">
            <p class="label">Temporary login email</p>
            <p class="value">{recipient_email}</p>
            <p class="label">Temporary password</p>
            <p class="value">{temp_password}</p>
          </div>
          <p>
            Please sign in and change your password as soon as possible to keep your account secure.
          </p>
          <p>Have a great day,<br><strong>Galala International School</strong></p>
        </div>
      </div>
    </div>
  </body>
</html>
"""
    message.add_alternative(html_body, subtype="html")
    try:
        with smtplib.SMTP(MAILPIT_HOST, MAILPIT_PORT, timeout=10) as smtp:
            smtp.send_message(message)
        return True
    except Exception:
        return False


@app.route("/")
def index():
    stats = {
        "students": count("SELECT COUNT(*) AS c FROM Student"),
        "teachers": count("SELECT COUNT(*) AS c FROM Instructor"),
        "assignments": count("SELECT COUNT(*) AS c FROM Assignment"),
        "activities": count("SELECT COUNT(*) AS c FROM Subject"),
    }
    return render_template("landing.html", stats=stats)


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = query("SELECT * FROM Users WHERE LOWER(Email)=%s", (email,), fetchone=True)
        if user and verify_password_and_upgrade_if_needed(user, password):
            login_user(user)
            flash(f"Welcome back, {user['Full_Name']}.", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        new_password = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")
        if not email or not new_password:
            flash("Email and new password are required.", "danger")
        elif new_password != confirm:
            flash("Passwords do not match.", "danger")
        elif len(new_password) < 8:
            flash("Password must be at least 8 characters.", "danger")
        else:
            user = query("SELECT User_ID FROM Users WHERE LOWER(Email)=%s", (email,), fetchone=True)
            if not user:
                flash("No account found with that email.", "danger")
            else:
                password_hash = bcrypt.generate_password_hash(new_password).decode("utf-8")
                execute("UPDATE Users SET Password_Hash=%s WHERE User_ID=%s", (password_hash, user["User_ID"]))
                flash("Password updated. Please log in.", "success")
                return redirect(url_for("login"))
    return render_template("forgot_password.html")


@app.route("/dashboard")
@login_required
def dashboard():
    if session.get("role") == "student":
        student_id = current_student_id()
        stats = {
            "total_students": count("SELECT COUNT(*) AS c FROM Studies WHERE Student_ID=%s", (student_id,)),
            "total_teachers": count("SELECT COUNT(DISTINCT a.Assignment_ID) AS c FROM Assignment a"),
            "total_assignments": count("SELECT COUNT(*) AS c FROM Assignment"),
            "top_students": count("SELECT COUNT(*) AS c FROM Submission WHERE Student_ID=%s AND Score IS NOT NULL", (student_id,)),
        }
        recent_enrollments = query(
            """
            SELECT Student_ID, CONCAT(Fname,' ',Lname) AS name, Level AS grade, Status, Enrolled_At
            FROM Student
            WHERE Student_ID=%s
            """,
            (student_id,),
        ) or []
    else:
        stats = {
            "total_students": count("SELECT COUNT(*) AS c FROM Student"),
            "total_teachers": count("SELECT COUNT(*) AS c FROM Instructor"),
            "total_assignments": count("SELECT COUNT(*) AS c FROM Assignment"),
            "top_students": count("SELECT COUNT(DISTINCT Student_ID) AS c FROM Studies WHERE Grade >= 90"),
        }
        recent_enrollments = query(
            """
            SELECT Student_ID, CONCAT(Fname,' ',Lname) AS name, Level AS grade, Status, Enrolled_At
            FROM Student
            ORDER BY Enrolled_At DESC
            LIMIT 6
            """
        ) or []
    upcoming_assignments = query(
        """
        SELECT a.Assignment_ID, a.Title, s.Subject_Name, a.Due_Date, a.Status
        FROM Assignment a
        JOIN Subject s ON a.Subject_ID=s.Subject_ID
        ORDER BY a.Due_Date ASC
        LIMIT 5
        """
    ) or []
    return render_template("dashboard.html", stats=stats, recent_enrollments=recent_enrollments, upcoming_assignments=upcoming_assignments)


@app.route("/students")
@role_required("teacher", "admin")
def students():
    search = request.args.get("q", "").strip()
    grade_filter = request.args.get("grade", "").strip()
    status_filter = request.args.get("status", "").strip()
    like_q = f"%{search}%"
    like_grade = f"%{grade_filter}%"
    rows = query(
        """
        SELECT Student_ID, Fname, Lname, Level, Batch_Year, Student_Email, Parent_Name,
               Parent_Pnum, Status, Enrolled_At
        FROM Student
        WHERE (%s='' OR Level LIKE %s)
          AND (%s='' OR Status=%s)
          AND (%s='' OR CONCAT(Fname,' ',Lname) LIKE %s OR Student_Email LIKE %s OR CAST(Student_ID AS CHAR) LIKE %s)
        ORDER BY Enrolled_At DESC
        """,
        (grade_filter, like_grade, status_filter, status_filter, search, like_q, like_q, like_q),
    ) or []
    return render_template("students.html", students=rows, search=search, grade_filter=grade_filter, status_filter=status_filter)


@app.route("/students/add", methods=["POST"])
@admin_required
def add_student():
    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    level = request.form.get("level", "").strip()
    parent_phone = request.form.get("parent_phone", "").strip()
    parent_name = request.form.get("parent_name", "").strip()
    if not full_name or not email:
        flash("Student name and email are required.", "danger")
        return redirect(url_for("students"))
    if query("SELECT User_ID FROM Users WHERE LOWER(Email)=%s", (email,), fetchone=True):
        flash("Email already exists.", "danger")
        return redirect(url_for("students"))
    temp_password = generate_temp_password()
    password_hash = bcrypt.generate_password_hash(temp_password).decode("utf-8")
    user_id = execute(
        "INSERT INTO Users (Full_Name,Email,Password_Hash,Role) VALUES (%s,%s,%s,'student')",
        (full_name, email, password_hash),
    )
    first, last = split_name(full_name)
    if user_id:
        execute(
            """
            INSERT INTO Student (User_ID,Fname,Lname,Level,Student_Email,Parent_Name,Parent_Pnum,Status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,'Pending')
            """,
            (user_id, first, last, level, email, parent_name, parent_phone),
        )
        email_sent = send_temporary_credentials_email(full_name, email, "student", temp_password)
        if email_sent:
            flash("Student added and temporary credentials sent by email.", "success")
        else:
            flash("Student added, but email delivery failed. Check Mailpit SMTP settings.", "warning")
    return redirect(url_for("students"))


@app.route("/students/edit/<int:student_id>", methods=["POST"])
@teacher_or_admin_required
def edit_student(student_id):
    full_name = request.form.get("full_name", "").strip()
    first, last = split_name(full_name)
    execute(
        """
        UPDATE Student
        SET Fname=%s, Lname=%s, Level=%s, Batch_Year=%s, Student_Email=%s,
            Parent_Name=%s, Parent_Pnum=%s, Status=%s
        WHERE Student_ID=%s
        """,
        (
            first,
            last,
            request.form.get("level") or None,
            request.form.get("batch_year") or None,
            request.form.get("email") or None,
            request.form.get("parent_name") or None,
            request.form.get("parent_phone") or None,
            request.form.get("status") or "Pending",
            student_id,
        ),
    )
    st = query("SELECT User_ID FROM Student WHERE Student_ID=%s", (student_id,), fetchone=True)
    if st and st.get("User_ID"):
        execute("UPDATE Users SET Full_Name=%s, Email=%s WHERE User_ID=%s", (full_name, request.form.get("email"), st["User_ID"]))
    flash("Student updated.", "success")
    return redirect(url_for("students"))


@app.route("/students/delete/<int:student_id>", methods=["POST"])
@admin_required
def delete_student(student_id):
    st = query("SELECT User_ID FROM Student WHERE Student_ID=%s", (student_id,), fetchone=True)
    if st and st.get("User_ID"):
        execute("DELETE FROM Users WHERE User_ID=%s", (st["User_ID"],))
    else:
        execute("DELETE FROM Student WHERE Student_ID=%s", (student_id,))
    flash("Student deleted.", "success")
    return redirect(url_for("students"))


@app.route("/student-profile")
@app.route("/student-profile/<int:student_id>")
@login_required
def student_profile(student_id=None):
    if student_id is None:
        student_id = current_student_id()
        if student_id is None:
            if session.get("role") == "student":
                flash("Your student profile is not connected yet. Contact an administrator.", "warning")
                return redirect(url_for("dashboard"))
            first_student = query("SELECT Student_ID FROM Student ORDER BY Enrolled_At DESC LIMIT 1", fetchone=True)
            if not first_student:
                flash("Add a student first to view a profile.", "info")
                return redirect(url_for("students"))
            student_id = first_student["Student_ID"]
    if session.get("role") == "student" and student_id != current_student_id():
        flash("You can only open your own student profile.", "danger")
        return redirect(url_for("student_profile"))
    student = query(
        """
        SELECT st.*, u.Email
        FROM Student st
        LEFT JOIN Users u ON st.User_ID=u.User_ID
        WHERE st.Student_ID=%s
        """,
        (student_id,),
        fetchone=True,
    )
    if not student:
        flash("Student not found.", "danger")
        return redirect(url_for("students"))
    grades = query(
        """
        SELECT sub.Subject_Name, st.Grade, st.Semester
        FROM Studies st
        JOIN Subject sub ON st.Subject_ID=sub.Subject_ID
        WHERE st.Student_ID=%s
        ORDER BY st.Semester DESC, sub.Subject_Name
        """,
        (student_id,),
    ) or []
    submissions = query(
        """
        SELECT su.Sub_ID, su.Submitted_At, su.Score, su.Feedback, su.File_Path,
               a.Title, a.Max_Score
        FROM Submission su
        JOIN Assignment a ON su.Assignment_ID=a.Assignment_ID
        WHERE su.Student_ID=%s
        ORDER BY su.Submitted_At DESC
        """,
        (student_id,),
    ) or []
    summary = query(
        """
        SELECT ROUND(AVG(Grade),2) AS avg_grade, COUNT(*) AS grade_count
        FROM Studies
        WHERE Student_ID=%s
        """,
        (student_id,),
        fetchone=True,
    ) or {}
    attendance = query(
        "SELECT COUNT(*) AS total, SUM(CASE WHEN Present THEN 1 ELSE 0 END) AS present FROM Attendance WHERE Student_ID=%s",
        (student_id,),
        fetchone=True,
    ) or {}
    attendance_rate = round(((attendance.get("present") or 0) / attendance["total"]) * 100, 1) if attendance.get("total") else 0
    return render_template("student_profile.html", student=student, grades=grades, submissions=submissions, summary=summary, attendance_rate=attendance_rate)


@app.route("/teachers")
@admin_required
def teachers():
    dept_filter = request.args.get("dept", "").strip()
    status_filter = request.args.get("status", "").strip()
    rows = query(
        """
        SELECT e.Emp_ID, e.Emp_FName, e.Emp_Lname, e.Emp_Email, e.Emp_Pnum,
               e.Employment_Date, e.Emp_Status, d.Dept_Name, i.Qualification,
               i.Specialization, COUNT(t.Subject_ID) AS subject_count
        FROM Employee e
        JOIN Instructor i ON e.Emp_ID=i.Emp_ID
        JOIN Department d ON e.Dept_ID=d.Dept_ID
        LEFT JOIN Teaches t ON i.Emp_ID=t.Emp_ID
        WHERE (%s='' OR d.Dept_Name=%s)
          AND (%s='' OR e.Emp_Status=%s)
        GROUP BY e.Emp_ID
        ORDER BY e.Emp_FName, e.Emp_Lname
        """,
        (dept_filter, dept_filter, status_filter, status_filter),
    ) or []
    departments = query("SELECT Dept_ID, Dept_Name FROM Department ORDER BY Dept_Name") or []
    subjects = query(
        """
        SELECT s.Subject_ID, s.Subject_Name, s.Subject_Level, d.Dept_Name
        FROM Subject s
        LEFT JOIN Department d ON s.Dept_ID=d.Dept_ID
        ORDER BY s.Subject_Name
        """
    ) or []
    return render_template("teachers.html", teachers=rows, departments=departments, subjects=subjects, dept_filter=dept_filter, status_filter=status_filter)


@app.route("/teachers/add", methods=["POST"])
@admin_required
def add_teacher():
    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    dept_id = request.form.get("dept_id") or ensure_department(request.form.get("department"))
    first, last = split_name(full_name)
    if not full_name or not email or not dept_id:
        flash("Teacher name, email, and department are required.", "danger")
        return redirect(url_for("teachers"))
    if query("SELECT User_ID FROM Users WHERE LOWER(Email)=%s", (email,), fetchone=True):
        flash("Email already exists.", "danger")
        return redirect(url_for("teachers"))
    temp_password = generate_temp_password()
    password_hash = bcrypt.generate_password_hash(temp_password).decode("utf-8")
    user_id = execute("INSERT INTO Users (Full_Name,Email,Password_Hash,Role) VALUES (%s,%s,%s,'teacher')", (full_name, email, password_hash))
    if user_id:
        emp_id = execute(
            """
            INSERT INTO Employee (User_ID,Emp_FName,Emp_Lname,Emp_Email,Emp_Pnum,Employment_Date,Emp_Status,Dept_ID)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (user_id, first, last, email, request.form.get("phone") or None, request.form.get("employment_date") or None, request.form.get("status") or "Active", dept_id),
        )
        if emp_id:
            execute(
                "INSERT INTO Instructor (Emp_ID,Qualification,Specialization) VALUES (%s,%s,%s)",
                (emp_id, request.form.get("qualification") or None, request.form.get("specialization") or None),
            )
            email_sent = send_temporary_credentials_email(full_name, email, "teacher", temp_password)
            if email_sent:
                flash("Teacher added and temporary credentials sent by email.", "success")
            else:
                flash("Teacher added, but email delivery failed. Check Mailpit SMTP settings.", "warning")
            return redirect(url_for("teachers"))
    flash("Teacher creation failed.", "danger")
    return redirect(url_for("teachers"))


@app.route("/teachers/edit/<int:emp_id>", methods=["POST"])
@admin_required
def edit_teacher(emp_id):
    full_name = request.form.get("full_name", "").strip()
    first, last = split_name(full_name)
    dept_id = request.form.get("dept_id") or ensure_department(request.form.get("department"))
    execute(
        """
        UPDATE Employee
        SET Emp_FName=%s, Emp_Lname=%s, Emp_Email=%s, Emp_Pnum=%s, Employment_Date=%s,
            Emp_Status=%s, Dept_ID=%s
        WHERE Emp_ID=%s
        """,
        (first, last, request.form.get("email") or None, request.form.get("phone") or None, request.form.get("employment_date") or None, request.form.get("status") or "Active", dept_id, emp_id),
    )
    execute(
        "UPDATE Instructor SET Qualification=%s, Specialization=%s WHERE Emp_ID=%s",
        (request.form.get("qualification") or None, request.form.get("specialization") or None, emp_id),
    )
    emp = query("SELECT User_ID FROM Employee WHERE Emp_ID=%s", (emp_id,), fetchone=True)
    if emp and emp.get("User_ID"):
        execute("UPDATE Users SET Full_Name=%s, Email=%s WHERE User_ID=%s", (full_name, request.form.get("email"), emp["User_ID"]))
    flash("Teacher updated.", "success")
    return redirect(url_for("teachers"))


@app.route("/teachers/delete/<int:emp_id>", methods=["POST"])
@admin_required
def delete_teacher(emp_id):
    emp = query("SELECT User_ID FROM Employee WHERE Emp_ID=%s", (emp_id,), fetchone=True)
    if emp and emp.get("User_ID"):
        execute("DELETE FROM Users WHERE User_ID=%s", (emp["User_ID"],))
    else:
        execute("DELETE FROM Employee WHERE Emp_ID=%s", (emp_id,))
    flash("Teacher deleted.", "success")
    return redirect(url_for("teachers"))


@app.route("/subjects/add", methods=["POST"])
@admin_required
def add_subject():
    name = request.form.get("subject_name", "").strip()
    if not name:
        flash("Subject name is required.", "danger")
        return redirect(request.referrer or url_for("teachers"))
    dept_id = request.form.get("dept_id") or ensure_department(request.form.get("department"))
    execute(
        "INSERT INTO Subject (Subject_Name, Subject_Level, Credits, Dept_ID) VALUES (%s,%s,%s,%s)",
        (name, request.form.get("subject_level") or None, request.form.get("credits") or 3, dept_id),
    )
    flash("Subject added.", "success")
    return redirect(request.referrer or url_for("teachers"))


@app.route("/assignments")
@login_required
def assignments():
    student_id = current_student_id()
    if session.get("role") == "student":
        rows = query(
            """
            SELECT a.Assignment_ID, a.Title, a.Description, a.Due_Date, a.Max_Score,
                   a.File_Path, a.Status, s.Subject_Name,
                   CONCAT(e.Emp_FName,' ',e.Emp_Lname) AS teacher_name,
                   su.Sub_ID, su.Score, su.Feedback, su.Submitted_At,
                   su.File_Path AS solution_file
            FROM Assignment a
            JOIN Subject s ON a.Subject_ID=s.Subject_ID
            LEFT JOIN Employee e ON a.Emp_ID=e.Emp_ID
            LEFT JOIN Submission su ON a.Assignment_ID=su.Assignment_ID AND su.Student_ID=%s
            ORDER BY a.Due_Date IS NULL, a.Due_Date ASC
            """,
            (student_id,),
        ) or []
        submissions = [row for row in rows if row.get("Sub_ID")]
    else:
        rows = query(
            """
            SELECT a.Assignment_ID, a.Title, a.Description, a.Due_Date, a.Max_Score,
                   a.File_Path, a.Status, s.Subject_Name,
                   CONCAT(e.Emp_FName,' ',e.Emp_Lname) AS teacher_name,
                   COUNT(DISTINCT sub.Sub_ID) AS submitted,
                   (SELECT COUNT(*) FROM Student) AS total_students
            FROM Assignment a
            JOIN Subject s ON a.Subject_ID=s.Subject_ID
            LEFT JOIN Employee e ON a.Emp_ID=e.Emp_ID
            LEFT JOIN Submission sub ON a.Assignment_ID=sub.Assignment_ID
            GROUP BY a.Assignment_ID
            ORDER BY a.Due_Date IS NULL, a.Due_Date ASC
            """
        ) or []
        submissions = query(
            """
            SELECT su.Sub_ID, su.Score, su.Feedback, su.Submitted_At, su.File_Path,
                   a.Title, CONCAT(st.Fname,' ',st.Lname) AS student_name
            FROM Submission su
            JOIN Assignment a ON su.Assignment_ID=a.Assignment_ID
            JOIN Student st ON su.Student_ID=st.Student_ID
            ORDER BY su.Submitted_At DESC
            LIMIT 30
            """
        ) or []
    subjects = query("SELECT Subject_ID, Subject_Name FROM Subject ORDER BY Subject_Name") or []
    stats = {"active": sum(1 for item in rows if item["Status"] == "Active"), "grading": sum(1 for item in rows if item["Status"] == "Grading"), "total": len(rows)}
    return render_template("assignments.html", assignments=rows, submissions=submissions, subjects=subjects, stats=stats, student_id=student_id)


@app.route("/assignments/create", methods=["POST"])
@teacher_or_admin_required
def create_assignment():
    title = request.form.get("title", "").strip()
    subject_id = request.form.get("subject_id")
    if not title or not subject_id:
        flash("Assignment title and subject are required.", "danger")
        return redirect(url_for("assignments"))
    execute(
        """
        INSERT INTO Assignment (Title,Description,Subject_ID,Emp_ID,Due_Date,Max_Score,File_Path,Status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,'Active')
        """,
        (
            title,
            request.form.get("description") or None,
            subject_id,
            current_teacher_id(),
            request.form.get("due_date") or None,
            request.form.get("max_score") or 100,
            safe_filename("assignment_file"),
        ),
    )
    flash("Assignment created.", "success")
    return redirect(url_for("assignments"))


@app.route("/assignments/submit/<int:assignment_id>", methods=["POST"])
@student_required
def submit_assignment(assignment_id):
    student_id = current_student_id()
    if not student_id:
        flash("Your account is not connected to a student profile.", "danger")
        return redirect(url_for("assignments"))
    execute(
        """
        INSERT INTO Submission (Assignment_ID,Student_ID,File_Path,Notes)
        VALUES (%s,%s,%s,%s)
        """,
        (assignment_id, student_id, safe_filename("solution_file"), request.form.get("notes") or None),
    )
    flash("Solution submitted.", "success")
    return redirect(url_for("assignments"))


@app.route("/assignments/grade/<int:sub_id>", methods=["POST"])
@teacher_or_admin_required
def grade_submission(sub_id):
    execute(
        "UPDATE Submission SET Score=%s, Feedback=%s WHERE Sub_ID=%s",
        (request.form.get("score") or None, request.form.get("feedback") or None, sub_id),
    )
    flash("Submission graded.", "success")
    return redirect(url_for("assignments"))


@app.route("/analytics")
@role_required("teacher", "admin")
def analytics():
    overview = query(
        """
        SELECT ROUND(AVG(Grade),1) AS avg_grade,
               (SELECT COUNT(*) FROM Student) AS total_students,
               (SELECT COUNT(*) FROM Instructor) AS total_teachers,
               (SELECT COUNT(*) FROM Assignment) AS total_assignments
        FROM Studies
        """,
        fetchone=True,
    ) or {}
    subject_perf = query(
        """
        SELECT sub.Subject_Name, ROUND(AVG(st.Grade),1) AS avg_grade, COUNT(st.Student_ID) AS student_count
        FROM Studies st
        JOIN Subject sub ON st.Subject_ID=sub.Subject_ID
        GROUP BY sub.Subject_ID
        ORDER BY avg_grade DESC
        """
    ) or []
    return render_template("analytics.html", overview=overview, subject_perf=subject_perf)


@app.route("/analytics/data")
@role_required("teacher", "admin")
def analytics_data():
    grade_dist = query(
        """
        SELECT
          SUM(CASE WHEN Grade>=90 THEN 1 ELSE 0 END) AS A_count,
          SUM(CASE WHEN Grade>=80 AND Grade<90 THEN 1 ELSE 0 END) AS B_count,
          SUM(CASE WHEN Grade>=70 AND Grade<80 THEN 1 ELSE 0 END) AS C_count,
          SUM(CASE WHEN Grade>=60 AND Grade<70 THEN 1 ELSE 0 END) AS D_count,
          SUM(CASE WHEN Grade<60 THEN 1 ELSE 0 END) AS F_count
        FROM Studies
        """,
        fetchone=True,
    ) or {}
    subject_perf = query(
        """
        SELECT sub.Subject_Name, ROUND(AVG(st.Grade),1) AS avg_grade
        FROM Studies st
        JOIN Subject sub ON st.Subject_ID=sub.Subject_ID
        GROUP BY sub.Subject_ID
        ORDER BY avg_grade DESC
        """
    ) or []
    assignment_completion = query(
        """
        SELECT a.Title, COUNT(su.Sub_ID) AS submitted, (SELECT COUNT(*) FROM Student) AS total_students
        FROM Assignment a
        LEFT JOIN Submission su ON a.Assignment_ID=su.Assignment_ID
        GROUP BY a.Assignment_ID
        ORDER BY a.Created_At DESC
        LIMIT 8
        """
    ) or []
    teacher_activity = query(
        """
        SELECT CONCAT(e.Emp_FName,' ',e.Emp_Lname) AS teacher_name, COUNT(a.Assignment_ID) AS assignments_created
        FROM Employee e
        JOIN Instructor i ON e.Emp_ID=i.Emp_ID
        LEFT JOIN Assignment a ON i.Emp_ID=a.Emp_ID
        GROUP BY e.Emp_ID
        ORDER BY assignments_created DESC
        LIMIT 8
        """
    ) or []
    monthly_stats = query(
        """
        SELECT DATE_FORMAT(Created_At, '%Y-%m') AS month_label, COUNT(*) AS total
        FROM Assignment
        GROUP BY DATE_FORMAT(Created_At, '%Y-%m')
        ORDER BY month_label ASC
        LIMIT 12
        """
    ) or []
    return jsonify(
        {
            "gradeDistribution": [
                grade_dist.get("A_count") or 0,
                grade_dist.get("B_count") or 0,
                grade_dist.get("C_count") or 0,
                grade_dist.get("D_count") or 0,
                grade_dist.get("F_count") or 0,
            ],
            "subjectLabels": [row["Subject_Name"] for row in subject_perf],
            "subjectScores": [float(row["avg_grade"] or 0) for row in subject_perf],
            "assignmentLabels": [row["Title"] for row in assignment_completion],
            "assignmentCompletion": [
                round(((row["submitted"] or 0) / row["total_students"]) * 100, 1) if row["total_students"] else 0
                for row in assignment_completion
            ],
            "teacherLabels": [row["teacher_name"] or "Unassigned" for row in teacher_activity],
            "teacherActivity": [row["assignments_created"] or 0 for row in teacher_activity],
            "monthlyLabels": [row["month_label"] for row in monthly_stats],
            "monthlyStats": [row["total"] or 0 for row in monthly_stats],
        }
    )


@app.route("/schedule")
@login_required
def schedule():
    entries = query(
        """
        SELECT se.Entry_ID, se.Day_Of_Week, TIME_FORMAT(se.Start_Time,'%H:%i') AS start_t,
               TIME_FORMAT(se.End_Time,'%H:%i') AS end_t, sub.Subject_Name,
               c.Classroom_Name, CONCAT(e.Emp_FName,' ',e.Emp_Lname) AS teacher_name
        FROM Schedule_Entry se
        JOIN Subject sub ON se.Subject_ID=sub.Subject_ID
        LEFT JOIN Classroom c ON se.Classroom_ID=c.Classroom_ID
        LEFT JOIN Employee e ON se.Emp_ID=e.Emp_ID
        ORDER BY FIELD(se.Day_Of_Week,'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'), se.Start_Time
        """
    ) or []
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    schedule_by_day = {day: [entry for entry in entries if entry["Day_Of_Week"] == day] for day in days}
    subjects = query("SELECT Subject_ID, Subject_Name FROM Subject ORDER BY Subject_Name") or []
    teachers_rows = query("SELECT Emp_ID, CONCAT(Emp_FName,' ',Emp_Lname) AS name FROM Employee ORDER BY Emp_FName") or []
    return render_template("schedule.html", days=days, schedule_by_day=schedule_by_day, subjects=subjects, teachers=teachers_rows)


@app.route("/schedule/add", methods=["POST"])
@admin_required
def add_schedule_entry():
    execute(
        """
        INSERT INTO Schedule_Entry (Subject_ID, Emp_ID, Day_Of_Week, Start_Time, End_Time)
        VALUES (%s,%s,%s,%s,%s)
        """,
        (
            request.form.get("subject_id"),
            request.form.get("emp_id") or current_teacher_id(),
            request.form.get("day"),
            request.form.get("start_time"),
            request.form.get("end_time"),
        ),
    )
    flash("Schedule entry added.", "success")
    return redirect(url_for("schedule"))


@app.route("/notifications")
@login_required
def notifications():
    rows = query(
        """
        SELECT * FROM Notification
        WHERE User_ID=%s OR User_ID IS NULL
        ORDER BY Created_At DESC
        """,
        (session.get("user_id"),),
    ) or []
    unread_count = sum(1 for row in rows if not row["Is_Read"])
    return render_template("Notifications.html", notifications=rows, unread_count=unread_count)


@app.route("/notifications/create", methods=["POST"])
@admin_required
def create_notification():
    execute(
        "INSERT INTO Notification (User_ID,Title,Message,Type) VALUES (%s,%s,%s,%s)",
        (
            request.form.get("user_id") or None,
            request.form.get("title"),
            request.form.get("message"),
            request.form.get("type") or "announcement",
        ),
    )
    flash("Notification published.", "success")
    return redirect(url_for("notifications"))


@app.route("/notifications/mark-read", methods=["POST"])
@login_required
def mark_notification_read():
    execute("UPDATE Notification SET Is_Read=TRUE WHERE User_ID=%s OR User_ID IS NULL", (session.get("user_id"),))
    return jsonify({"status": "ok"})


@app.route("/admin-dashboard")
@admin_required
def admin_dashboard():
    pending_regs = query("SELECT * FROM Online_Registration ORDER BY Submitted_At DESC") or []
    user_dist_rows = query("SELECT Role, COUNT(*) AS cnt FROM Users GROUP BY Role") or []
    system_stats = {
        "students": count("SELECT COUNT(*) AS c FROM Student"),
        "teachers": count("SELECT COUNT(*) AS c FROM Instructor"),
        "assignments": count("SELECT COUNT(*) AS c FROM Assignment"),
        "pending_regs": count("SELECT COUNT(*) AS c FROM Online_Registration WHERE Status='Pending'"),
        "notifications": count("SELECT COUNT(*) AS c FROM Notification"),
    }
    return render_template("admin_dashboard.html", pending_regs=pending_regs, user_dist={row["Role"]: row["cnt"] for row in user_dist_rows}, system_stats=system_stats)


@app.route("/admin/registration/<int:reg_id>/<action>", methods=["POST"])
@admin_required
def handle_registration(reg_id, action):
    if action not in ("approve", "reject"):
        flash("Unknown registration action.", "danger")
        return redirect(url_for("admin_dashboard"))
    status = "Approved" if action == "approve" else "Rejected"
    execute("UPDATE Online_Registration SET Status=%s WHERE Reg_ID=%s", (status, reg_id))
    flash(f"Registration {status.lower()}.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/online-registration", methods=["GET", "POST"])
def online_registration():
    if request.method == "POST":
        required = ["full_name", "birth_date", "gender", "nationality", "grade", "parent_name", "parent_phone", "parent_email", "address"]
        missing = [field.replace("_", " ").title() for field in required if not request.form.get(field)]
        if missing:
            flash("Please complete: " + ", ".join(missing), "danger")
            return render_template("online_registration.html")
        execute(
            """
            INSERT INTO Online_Registration
            (Full_Name,Birth_Date,Gender,Nationality,Email,Phone,Grade_Applied,Parent_Name,
             Parent_Phone,Parent_Email,Address,Previous_School,Birth_Certificate,Student_Photo,
             Previous_Transcript,Notes)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                request.form.get("full_name"),
                request.form.get("birth_date"),
                request.form.get("gender"),
                request.form.get("nationality"),
                request.form.get("parent_email"),
                request.form.get("parent_phone"),
                request.form.get("grade"),
                request.form.get("parent_name"),
                request.form.get("parent_phone"),
                request.form.get("parent_email"),
                request.form.get("address"),
                request.form.get("previous_school") or None,
                safe_filename("birth_certificate"),
                safe_filename("student_photo"),
                safe_filename("previous_transcript"),
                request.form.get("notes") or None,
            ),
        )
        flash("Registration submitted successfully. The admissions team will review it.", "success")
        return redirect(url_for("online_registration"))
    return render_template("online_registration.html")


def fallback_ai(question):
    text = question.lower()
    if "top" in text and "student" in text:
        return {
            "sql": """
                SELECT st.Student_ID, CONCAT(st.Fname,' ',st.Lname) AS student_name, ROUND(AVG(s.Grade),2) AS average_grade
                FROM Student st JOIN Studies s ON st.Student_ID=s.Student_ID
                GROUP BY st.Student_ID
                ORDER BY average_grade DESC
                LIMIT 10
            """,
            "explanation": "Shows the students with the highest average grades.",
        }
    if "failed" in text and "math" in text:
        return {
            "sql": """
                SELECT st.Student_ID, CONCAT(st.Fname,' ',st.Lname) AS student_name, sub.Subject_Name, s.Grade
                FROM Student st
                JOIN Studies s ON st.Student_ID=s.Student_ID
                JOIN Subject sub ON s.Subject_ID=sub.Subject_ID
                WHERE s.Grade < 60 AND LOWER(sub.Subject_Name) LIKE '%math%'
                ORDER BY s.Grade ASC
                LIMIT 50
            """,
            "explanation": "Lists students with failing Math grades.",
        }
    if "best" in text and ("class" in text or "subject" in text):
        return {
            "sql": """
                SELECT sub.Subject_Name, ROUND(AVG(s.Grade),2) AS average_grade, COUNT(s.Student_ID) AS student_count
                FROM Subject sub JOIN Studies s ON sub.Subject_ID=s.Subject_ID
                GROUP BY sub.Subject_ID
                ORDER BY average_grade DESC
                LIMIT 10
            """,
            "explanation": "Ranks subjects by average student performance.",
        }
    if "submitted this week" in text:
        return {
            "sql": """
                SELECT a.Title, CONCAT(st.Fname,' ',st.Lname) AS student_name, su.Submitted_At
                FROM Submission su
                JOIN Assignment a ON su.Assignment_ID=a.Assignment_ID
                JOIN Student st ON su.Student_ID=st.Student_ID
                WHERE YEARWEEK(su.Submitted_At, 1)=YEARWEEK(CURDATE(), 1)
                ORDER BY su.Submitted_At DESC
                LIMIT 50
            """,
            "explanation": "Lists assignment submissions received this week.",
        }
    return {
        "sql": "SELECT Student_ID, Fname, Lname, Level, Status FROM Student ORDER BY Enrolled_At DESC LIMIT 50",
        "explanation": "Shows the latest student records.",
    }


def generate_sql(question):
    if not ai_client:
        return fallback_ai(question)
    prompt = DB_SCHEMA + f'\nUser question: "{question}"'
    response = ai_client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    raw = response.text.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


@app.route("/ai-assistant")
@role_required("teacher", "admin")
def ai_assistant():
    return render_template("ai_assistant.html")


@app.route("/ai-assistant/query", methods=["POST"])
@role_required("teacher", "admin")
def ai_query():
    question = (request.json or {}).get("question", "").strip()
    if not question:
        return jsonify({"error": "Question is required."}), 400
    try:
        ai_json = generate_sql(question)
        sql_query = (ai_json.get("sql") or "").strip().rstrip(";")
        if not re.match(r"^select\b", sql_query, re.IGNORECASE):
            return jsonify({"error": "Only SELECT queries are allowed."}), 400
        if re.search(r"\b(insert|update|delete|drop|alter|truncate|create|replace)\b", sql_query, re.IGNORECASE):
            return jsonify({"error": "Unsafe SQL keyword detected."}), 400
        rows = query(sql_query) or []
        columns = list(rows[0].keys()) if rows else []
        return jsonify(
            {
                "explanation": ai_json.get("explanation") or "Query completed.",
                "sql": sql_query,
                "columns": columns,
                "rows": [list(row.values()) for row in rows],
                "count": len(rows),
            }
        )
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.errorhandler(404)
def not_found(_error):
    return render_template("landing.html", stats={"students": 0, "teachers": 0, "assignments": 0, "activities": 0}), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("landing.html", stats={"students": 0, "teachers": 0, "assignments": 0, "activities": 0}, server_error=str(error)), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
