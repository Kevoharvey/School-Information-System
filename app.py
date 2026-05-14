from functools import wraps
import html
import json
import os
import re
import secrets
import smtplib
from datetime import date
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
TEMP_EMAIL_DOMAIN = os.environ.get("TEMP_EMAIL_DOMAIN", "galala.local")

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
Online_Registration(Reg_ID, Applicant_Type, Full_Name, Birth_Date, Gender, Nationality, Email, Phone, Grade_Applied, Parent_Name, Parent_Phone, Parent_Email, Address, Previous_School, Birth_Certificate, Student_Photo, Previous_Transcript, Department, Qualification, Specialization, Employment_Date, Notes, Status, Submitted_At)
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
    role = session.get("role")
    user_id = session.get("user_id")
    user_photo = None
    if role == "student" and user_id:
        row = query("SELECT Student_Photo FROM Student WHERE User_ID=%s", (user_id,), fetchone=True)
        if row:
            user_photo = row.get("Student_Photo")
    return {
        "current_user": session.get("email"),
        "user_name": session.get("name"),
        "user_role": role,
        "user_id": user_id,
        "user_photo": user_photo,
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


def ensure_registration_schema():
    pass

REGISTRATION_UNION_QUERY = """
SELECT 
    Student_Reg_ID AS Reg_ID,
    'student' AS Applicant_Type,
    Full_Name, Birth_Date, Gender, Nationality, Email, Phone,
    Grade_Applied, Parent_Name, Parent_Phone, Parent_Email,
    Address, Previous_School, Birth_Certificate, Student_Photo,
    Previous_Transcript, NULL AS Department, NULL AS Qualification,
    NULL AS Specialization, NULL AS Employment_Date, Notes, Status, Submitted_At
FROM Student_Registration
UNION ALL
SELECT 
    Teacher_Reg_ID AS Reg_ID,
    'teacher' AS Applicant_Type,
    Full_Name, NULL, NULL, NULL, Contact_Email, Phone_Number,
    NULL, NULL, NULL, NULL,
    Address, NULL, NULL, NULL,
    NULL, Department, Qualification,
    Specialization, Available_Start_Date, Notes, Status, Submitted_At
FROM Teacher_Registration
"""


def split_name(full_name):
    parts = (full_name or "").strip().split()
    first = parts[0] if parts else ""
    last = " ".join(parts[1:]) if len(parts) > 1 else first
    return first, last


def year_label(value):
    label = (value or "").strip()
    return label or "No year assigned"


def year_sort_key(label):
    match = re.search(r"\d+", label or "")
    if match:
        return (0, int(match.group()), label.lower())
    if "kindergarten" in (label or "").lower():
        return (-1, 0, label.lower())
    return (1, 0, (label or "").lower())


def group_by_year(rows, key):
    grouped = {}
    for row in rows or []:
        label = year_label(row.get(key))
        grouped.setdefault(label, []).append(row)
    return [(label, grouped[label]) for label in sorted(grouped, key=year_sort_key)]


def ensure_department(name):
    dept_name = (name or "General").strip() or "General"
    row = query("SELECT Dept_ID FROM Department WHERE Dept_Name=%s", (dept_name,), fetchone=True)
    if row:
        return row["Dept_ID"]
    return execute("INSERT INTO Department (Dept_Name) VALUES (%s)", (dept_name,))


def ensure_classroom(name):
    room_name = (name or "").strip()
    if not room_name:
        return None
    row = query("SELECT Classroom_ID FROM Classroom WHERE Classroom_Name=%s", (room_name,), fetchone=True)
    if row:
        return row["Classroom_ID"]
    execute("INSERT INTO Classroom (Classroom_Name) VALUES (%s)", (room_name,))
    row = query("SELECT Classroom_ID FROM Classroom WHERE Classroom_Name=%s", (room_name,), fetchone=True)
    return row["Classroom_ID"] if row else None


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


def slugify_email_part(value):
    slug = re.sub(r"[^a-z0-9]+", ".", (value or "").strip().lower())
    slug = slug.strip(".")
    return slug or "user"


def generate_temp_login_email(full_name, role):
    base = f"{role}.{slugify_email_part(full_name)}"
    domain = TEMP_EMAIL_DOMAIN.strip().lower() or "galala.local"
    for index in range(1000):
        suffix = "" if index == 0 else str(index + 1)
        candidate = f"{base}{suffix}@{domain}"
        if not query("SELECT User_ID FROM Users WHERE LOWER(Email)=%s", (candidate.lower(),), fetchone=True):
            return candidate
    return f"{base}.{secrets.token_hex(3)}@{domain}"


def send_email(recipient_email, subject, text_body, html_body=None):
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = MAIL_FROM
    message["To"] = recipient_email
    message.set_content(text_body)
    if html_body:
        message.add_alternative(html_body, subtype="html")
    try:
        with smtplib.SMTP(MAILPIT_HOST, MAILPIT_PORT, timeout=10) as smtp:
            smtp.send_message(message)
        return True
    except Exception:
        return False


def send_temporary_credentials_email(recipient_name, recipient_email, role, temp_password, login_email=None):
    login_email = login_email or recipient_email
    safe_name = html.escape(recipient_name or "there")
    safe_role = html.escape(role or "user")
    safe_login = html.escape(login_email)
    safe_password = html.escape(temp_password)
    text_body = f"""Hello {recipient_name},

Welcome to Galala International School.
Your {role} account was created by the administration team.

Temporary login email: {login_email}
Temporary password: {temp_password}

Please log in and change your password as soon as possible.

Best regards,
Galala International School
"""
    subject = "Welcome to Galala International School"
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
          <p>Hello {safe_name},</p>
          <p>
            We are happy to have you with us. Your <strong>{safe_role}</strong> account has been created by the school administration team.
          </p>
          <div class="credentials">
            <p class="label">Temporary login email</p>
            <p class="value">{safe_login}</p>
            <p class="label">Temporary password</p>
            <p class="value">{safe_password}</p>
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
    return send_email(recipient_email, subject, text_body, html_body)


def send_registration_rejection_email(recipient_name, recipient_email, applicant_type):
    safe_name = html.escape(recipient_name or "there")
    safe_type = html.escape((applicant_type or "application").title())
    text_body = f"""Hello {recipient_name},

Thank you for applying to Galala International School.

After reviewing your {applicant_type} registration, we are sorry that we cannot approve it at this time. We truly appreciate the time you took to apply, and you are welcome to contact the admissions office if you would like more details.

Warm regards,
Galala International School
"""
    html_body = f"""
<!doctype html>
<html>
  <body style="margin:0;background:#f4f7fb;font-family:Arial,Helvetica,sans-serif;color:#1f2937;">
    <div style="padding:24px 12px;">
      <div style="max-width:640px;margin:0 auto;background:#ffffff;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;">
        <div style="background:#1f4fd8;color:#ffffff;padding:22px 26px;">
          <h1 style="margin:0;font-size:22px;">Registration Update</h1>
        </div>
        <div style="padding:24px 26px;line-height:1.6;font-size:15px;">
          <p>Hello {safe_name},</p>
          <p>Thank you for applying to Galala International School.</p>
          <p>After reviewing your <strong>{safe_type}</strong> registration, we are sorry that we cannot approve it at this time.</p>
          <p>We truly appreciate the time you took to apply, and you are welcome to contact the admissions office if you would like more details.</p>
          <p>Warm regards,<br><strong>Galala International School</strong></p>
        </div>
      </div>
    </div>
  </body>
</html>
"""
    return send_email(recipient_email, "Your Galala International School registration update", text_body, html_body)


def send_registration_received_email(recipient_name, recipient_email):
    safe_name = html.escape(recipient_name or "there")
    text_body = f"""Hello {recipient_name},

Thank you for your registration. We have received your application and our admissions team is currently reviewing it.
We will work on your application and send the decision within 2 days. Please follow your email for updates.

Best regards,
Galala International School
"""
    html_body = f"""
<!doctype html>
<html>
  <body style="margin:0;background:#f4f7fb;font-family:Arial,Helvetica,sans-serif;color:#1f2937;">
    <div style="padding:24px 12px;">
      <div style="max-width:640px;margin:0 auto;background:#ffffff;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;">
        <div style="background:#1f4fd8;color:#ffffff;padding:22px 26px;">
          <h1 style="margin:0;font-size:22px;">Registration Received</h1>
        </div>
        <div style="padding:24px 26px;line-height:1.6;font-size:15px;">
          <p>Hello {safe_name},</p>
          <p>Thank you for your registration.</p>
          <p>We have received your application and our admissions team is currently reviewing it. We will work on your application and send the decision within 2 days. Please follow your email for updates.</p>
          <p>Best regards,<br><strong>Galala International School</strong></p>
        </div>
      </div>
    </div>
  </body>
</html>
"""
    return send_email(recipient_email, "Application Received - Galala International School", text_body, html_body)


def send_student_expulsion_email(student_name, recipient_email, deletion_reason):
    safe_name = html.escape(student_name or "there")
    safe_reason = html.escape(deletion_reason or "No reason was provided.").replace("\n", "<br>")
    text_body = f"""Hello {student_name},

We are writing to let you know that your enrollment at Galala International School has been ended, and your student account has been removed from the school system.

Reason provided by the administration:
{deletion_reason}

If you or your family have questions about this decision, please contact the school administration office. We wish you the very best in your next step.

Regards,
Galala International School
"""
    html_body = f"""
<!doctype html>
<html>
  <body style="margin:0;background:#f4f7fb;font-family:Arial,Helvetica,sans-serif;color:#1f2937;">
    <div style="padding:24px 12px;">
      <div style="max-width:640px;margin:0 auto;background:#ffffff;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;">
        <div style="background:#b42318;color:#ffffff;padding:22px 26px;">
          <h1 style="margin:0;font-size:22px;">Enrollment Update</h1>
        </div>
        <div style="padding:24px 26px;line-height:1.6;font-size:15px;">
          <p>Hello {safe_name},</p>
          <p>We are writing to let you know that your enrollment at Galala International School has been ended, and your student account has been removed from the school system.</p>
          <div style="margin:16px 0;padding:14px 16px;border:1px solid #f4c7c3;background:#fff5f5;border-radius:10px;">
            <p style="margin:0 0 6px;font-size:13px;color:#667085;font-weight:bold;">Reason provided by the administration</p>
            <p style="margin:0;">{safe_reason}</p>
          </div>
          <p>If you or your family have questions about this decision, please contact the school administration office.</p>
          <p>We wish you the very best in your next step.</p>
          <p>Regards,<br><strong>Galala International School</strong></p>
        </div>
      </div>
    </div>
  </body>
</html>
"""
    return send_email(recipient_email, "Your Galala International School enrollment update", text_body, html_body)


def registration_contact_email(registration):
    applicant_type = (registration.get("Applicant_Type") or "student").lower()
    if applicant_type == "student":
        return registration.get("Parent_Email") or registration.get("Email")
    return registration.get("Email") or registration.get("Parent_Email")


def create_student_from_registration(registration):
    full_name = registration.get("Full_Name") or ""
    login_email = generate_temp_login_email(full_name, "student")
    temp_password = generate_temp_password()
    password_hash = bcrypt.generate_password_hash(temp_password).decode("utf-8")
    user_id = execute(
        "INSERT INTO Users (Full_Name,Email,Password_Hash,Role) VALUES (%s,%s,%s,'student')",
        (full_name, login_email, password_hash),
    )
    if not user_id:
        return None, None
    first, last = split_name(full_name)
    student_id = execute(
        """
        INSERT INTO Student
        (User_ID,Fname,Lname,Level,Batch_Year,Birth_Date,Gender,Nationality,Student_Email,Student_Pnum,
         Parent_Name,Parent_Pnum,Parent_Email,Student_Address,Previous_School,Student_Photo,
         Birth_Certificate,Previous_Transcript,Notes,Status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'Enrolled')
        """,
        (
            user_id,
            first,
            last,
            registration.get("Grade_Applied"),
            date.today().year,
            registration.get("Birth_Date"),
            registration.get("Gender"),
            registration.get("Nationality"),
            login_email,
            registration.get("Phone"),
            registration.get("Parent_Name"),
            registration.get("Parent_Phone"),
            registration.get("Parent_Email"),
            registration.get("Address"),
            registration.get("Previous_School"),
            registration.get("Student_Photo"),
            registration.get("Birth_Certificate"),
            registration.get("Previous_Transcript"),
            registration.get("Notes"),
        ),
    )
    return (login_email, temp_password) if student_id else (None, None)


def create_teacher_from_registration(registration):
    full_name = registration.get("Full_Name") or ""
    login_email = generate_temp_login_email(full_name, "teacher")
    temp_password = generate_temp_password()
    password_hash = bcrypt.generate_password_hash(temp_password).decode("utf-8")
    user_id = execute(
        "INSERT INTO Users (Full_Name,Email,Password_Hash,Role) VALUES (%s,%s,%s,'teacher')",
        (full_name, login_email, password_hash),
    )
    if not user_id:
        return None, None
    first, last = split_name(full_name)
    dept_id = ensure_department(registration.get("Department") or "General")
    emp_id = execute(
        """
        INSERT INTO Employee (User_ID,Emp_FName,Emp_Lname,Emp_Email,Emp_Pnum,Employment_Date,Emp_Status,Dept_ID)
        VALUES (%s,%s,%s,%s,%s,%s,'Active',%s)
        """,
        (
            user_id,
            first,
            last,
            login_email,
            registration.get("Phone"),
            registration.get("Employment_Date"),
            dept_id,
        ),
    )
    if not emp_id:
        return None, None
    execute(
        "INSERT INTO Instructor (Emp_ID,Qualification,Specialization) VALUES (%s,%s,%s)",
        (emp_id, registration.get("Qualification"), registration.get("Specialization")),
    )
    return login_email, temp_password


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
        ORDER BY Level, Enrolled_At DESC
        """,
        (grade_filter, like_grade, status_filter, status_filter, search, like_q, like_q, like_q),
    ) or []
    students_by_year = group_by_year(rows, "Level")
    # For teachers: only subjects they teach; for admins: all subjects
    if session.get("role") == "teacher":
        teacher_id = current_teacher_id()
        subjects = query(
            """
            SELECT s.Subject_ID, s.Subject_Name
            FROM Subject s
            JOIN Teaches t ON s.Subject_ID = t.Subject_ID
            WHERE t.Emp_ID = %s
            ORDER BY s.Subject_Name
            """,
            (teacher_id,),
        ) or []
    else:
        subjects = query("SELECT Subject_ID, Subject_Name FROM Subject ORDER BY Subject_Name") or []
    return render_template(
        "students.html",
        students=rows,
        students_by_year=students_by_year,
        search=search,
        grade_filter=grade_filter,
        status_filter=status_filter,
        subjects=subjects,
    )


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
@admin_required
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
    deletion_reason = (request.form.get("deletion_reason") or "").strip()
    if not deletion_reason:
        flash("Please provide a reason before deleting a student.", "danger")
        return redirect(url_for("students"))

    st = query(
        """
        SELECT st.User_ID, st.Fname, st.Lname, st.Student_Email, st.Parent_Email, u.Email AS User_Email
        FROM Student st
        LEFT JOIN Users u ON st.User_ID=u.User_ID
        WHERE st.Student_ID=%s
        """,
        (student_id,),
        fetchone=True,
    )
    if not st:
        flash("Student not found.", "danger")
        return redirect(url_for("students"))

    student_name = f"{st.get('Fname') or ''} {st.get('Lname') or ''}".strip() or "Student"
    recipient_email = st.get("Student_Email") or st.get("User_Email") or st.get("Parent_Email")
    email_sent = send_student_expulsion_email(student_name, recipient_email, deletion_reason) if recipient_email else False
    if st and st.get("User_ID"):
        execute("DELETE FROM Users WHERE User_ID=%s", (st["User_ID"],))
    else:
        execute("DELETE FROM Student WHERE Student_ID=%s", (student_id,))
        
    # Also delete the associated online registration record to keep the review page clean
    execute(
        "DELETE FROM Student_Registration WHERE Full_Name=%s OR Email=%s OR Parent_Email=%s",
        (student_name, st.get("User_Email") or "N/A", st.get("Parent_Email") or "N/A")
    )
    
    if email_sent:
        flash("Student deleted from the database and expulsion email sent.", "success")
    else:
        flash("Student deleted from the database, but the expulsion email could not be sent. Check Mailpit settings.", "warning")
    return redirect(url_for("students"))


@app.route("/students/expel-from-subject/<int:student_id>", methods=["POST"])
@teacher_or_admin_required
def expel_from_subject(student_id):
    subject_id = request.form.get("subject_id")
    semester = request.form.get("semester", "").strip() or None
    if not subject_id:
        flash("No subject selected.", "danger")
        return redirect(url_for("students"))

    # Teachers may only expel from subjects they teach
    if session.get("role") == "teacher":
        teacher_id = current_teacher_id()
        if not teacher_id:
            flash("Teacher profile not found.", "danger")
            return redirect(url_for("students"))
        teaches = query(
            "SELECT 1 FROM Teaches WHERE Emp_ID=%s AND Subject_ID=%s",
            (teacher_id, subject_id),
            fetchone=True,
        )
        if not teaches:
            flash("You can only expel students from subjects you teach.", "danger")
            return redirect(url_for("students"))

    if semester:
        execute(
            "DELETE FROM Studies WHERE Student_ID=%s AND Subject_ID=%s AND Semester=%s",
            (student_id, subject_id, semester),
        )
    else:
        execute(
            "DELETE FROM Studies WHERE Student_ID=%s AND Subject_ID=%s",
            (student_id, subject_id),
        )

    subject = query("SELECT Subject_Name FROM Subject WHERE Subject_ID=%s", (subject_id,), fetchone=True)
    subject_name = subject["Subject_Name"] if subject else "the subject"
    flash(f"Student removed from {subject_name}.", "success")
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
@teacher_or_admin_required
def teachers():
    dept_filter = request.args.get("dept", "").strip()
    status_filter = request.args.get("status", "").strip()
    rows = query(
        """
        SELECT e.Emp_ID, e.Emp_FName, e.Emp_Lname, e.Emp_Email, e.Emp_Pnum,
               e.Employment_Date, e.Emp_Status, d.Dept_Name, i.Qualification,
               i.Specialization, COUNT(DISTINCT t.Subject_ID) AS subject_count
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
    return render_template("academic.html", teachers=rows, departments=departments, subjects=subjects, dept_filter=dept_filter, status_filter=status_filter)


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
@teacher_or_admin_required
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
    departments = query("SELECT Dept_ID, Dept_Name FROM Department ORDER BY Dept_Name") or []
    stats = {"active": sum(1 for item in rows if item["Status"] == "Active"), "grading": sum(1 for item in rows if item["Status"] == "Grading"), "total": len(rows)}
    return render_template("assignments.html", assignments=rows, submissions=submissions, subjects=subjects, departments=departments, stats=stats, student_id=student_id)


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
    
    # Notify all students about the new assignment
    all_students = query("SELECT User_ID FROM Student WHERE User_ID IS NOT NULL") or []
    for s in all_students:
        execute(
            "INSERT INTO Notification (User_ID, Title, Message, Type) VALUES (%s, %s, %s, 'system')",
            (s["User_ID"], "New Assignment", f"A new assignment '{title}' has been added.")
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

    # Update the parent Assignment status to "Grading" to reflect the stat counter
    execute(
        """
        UPDATE Assignment SET Status='Grading'
        WHERE Assignment_ID = (
            SELECT Assignment_ID FROM Submission WHERE Sub_ID=%s
        ) AND Status = 'Active'
        """,
        (sub_id,),
    )

    # Sync grade into the Studies table so the student profile Grades Table is populated
    score = request.form.get("score") or None
    if score:
        sub_data = query(
            """
            SELECT su.Student_ID, a.Subject_ID
            FROM Submission su
            JOIN Assignment a ON su.Assignment_ID = a.Assignment_ID
            WHERE su.Sub_ID = %s
            """,
            (sub_id,),
            fetchone=True,
        )
        if sub_data:
            existing = query(
                "SELECT Student_ID FROM Studies WHERE Student_ID=%s AND Subject_ID=%s AND Semester='CURRENT'",
                (sub_data["Student_ID"], sub_data["Subject_ID"]),
                fetchone=True,
            )
            if existing:
                execute(
                    "UPDATE Studies SET Grade=%s WHERE Student_ID=%s AND Subject_ID=%s AND Semester='CURRENT'",
                    (score, sub_data["Student_ID"], sub_data["Subject_ID"]),
                )
            else:
                execute(
                    "INSERT INTO Studies (Student_ID, Subject_ID, Grade, Semester) VALUES (%s,%s,%s,'CURRENT')",
                    (sub_data["Student_ID"], sub_data["Subject_ID"], score),
                )

    # Notify the student that their assignment was graded
    sub_info = query(
        """
        SELECT a.Title, st.User_ID
        FROM Submission su
        JOIN Assignment a ON su.Assignment_ID = a.Assignment_ID
        JOIN Student st ON su.Student_ID = st.Student_ID
        WHERE su.Sub_ID = %s
        """,
        (sub_id,),
        fetchone=True
    )
    if sub_info and sub_info.get("User_ID"):
        execute(
            "INSERT INTO Notification (User_ID, Title, Message, Type) VALUES (%s, %s, %s, 'system')",
            (sub_info["User_ID"], "Assignment Graded", f"Your submission for '{sub_info['Title']}' has been graded.")
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
@teacher_or_admin_required
def add_schedule_entry():
    classroom_id = ensure_classroom(request.form.get("room"))
    subject_id = request.form.get("subject_id")
    emp_id = request.form.get("emp_id") or current_teacher_id()
    
    execute(
        """
        INSERT INTO Schedule_Entry (Subject_ID, Emp_ID, Classroom_ID, Day_Of_Week, Start_Time, End_Time)
        VALUES (%s,%s,%s,%s,%s,%s)
        """,
        (
            subject_id,
            emp_id,
            classroom_id,
            request.form.get("day"),
            request.form.get("start_time"),
            request.form.get("end_time"),
        ),
    )
    # Sync the subject to the teacher's profile so the count increments
    try:
        execute("INSERT IGNORE INTO Teaches (Emp_ID, Subject_ID) VALUES (%s, %s)", (emp_id, subject_id))
    except Exception:
        pass
        
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


# ─────────────────────────────────────────────
#  ATTENDANCE
# ─────────────────────────────────────────────

@app.route("/attendance")
@teacher_or_admin_required
def attendance():
    """Attendance overview — pick a subject and date."""
    # Show all subjects to both teachers and admins
    subjects = query("SELECT Subject_ID, Subject_Name FROM Subject ORDER BY Subject_Name") or []

    subject_id = request.args.get("subject_id", "")
    att_date = request.args.get("att_date", str(date.today()))

    students = []
    subject_name = ""
    existing_attendance = {}

    if subject_id:
        subj_row = query("SELECT Subject_Name FROM Subject WHERE Subject_ID=%s", (subject_id,), fetchone=True)
        subject_name = subj_row["Subject_Name"] if subj_row else ""

        students = query(
            """
            SELECT st.Student_ID, st.Fname, st.Lname, st.Student_Email
            FROM Student st
            ORDER BY st.Fname, st.Lname
            """,
        ) or []

        existing_rows = query(
            "SELECT Student_ID, Present FROM Attendance WHERE Subject_ID=%s AND Att_Date=%s",
            (subject_id, att_date),
        ) or []
        existing_attendance = {row["Student_ID"]: row["Present"] for row in existing_rows}

    # Summary stats per subject for the overview table
    summary = query(
        """
        SELECT s.Subject_ID, s.Subject_Name,
               COUNT(DISTINCT a.Att_Date) AS sessions,
               COUNT(a.Att_ID) AS total_records,
               SUM(CASE WHEN a.Present THEN 1 ELSE 0 END) AS present_count
        FROM Subject s
        LEFT JOIN Attendance a ON s.Subject_ID = a.Subject_ID
        GROUP BY s.Subject_ID
        ORDER BY s.Subject_Name
        """
    ) or []

    return render_template(
        "attendance.html",
        subjects=subjects,
        subject_id=subject_id,
        subject_name=subject_name,
        att_date=att_date,
        students=students,
        existing_attendance=existing_attendance,
        summary=summary,
    )


@app.route("/attendance/save", methods=["POST"])
@teacher_or_admin_required
def save_attendance():
    subject_id = request.form.get("subject_id")
    att_date = request.form.get("att_date") or str(date.today())

    if not subject_id:
        flash("No subject selected.", "danger")
        return redirect(url_for("attendance"))

    # Get all students that were shown in the form
    all_student_ids = request.form.getlist("all_students")
    present_ids = set(request.form.getlist("present"))

    for sid in all_student_ids:
        is_present = sid in present_ids
        existing = query(
            "SELECT Att_ID FROM Attendance WHERE Student_ID=%s AND Subject_ID=%s AND Att_Date=%s",
            (sid, subject_id, att_date),
            fetchone=True,
        )
        if existing:
            execute(
                "UPDATE Attendance SET Present=%s WHERE Att_ID=%s",
                (is_present, existing["Att_ID"]),
            )
        else:
            execute(
                "INSERT INTO Attendance (Student_ID, Subject_ID, Att_Date, Present) VALUES (%s,%s,%s,%s)",
                (sid, subject_id, att_date, is_present),
            )

    flash(f"Attendance saved for {att_date}.", "success")
    return redirect(url_for("attendance", subject_id=subject_id, att_date=att_date))


@app.route("/notifications/mark-read", methods=["POST"])
@login_required
def mark_notification_read():
    execute("UPDATE Notification SET Is_Read=TRUE WHERE User_ID=%s OR User_ID IS NULL", (session.get("user_id"),))
    return jsonify({"status": "ok"})


@app.route("/admin-dashboard")
@admin_required
def admin_dashboard():
    ensure_registration_schema()
    pending_regs = query(f"SELECT * FROM ({REGISTRATION_UNION_QUERY}) AS r ORDER BY Submitted_At DESC LIMIT 8") or []
    user_dist_rows = query("SELECT Role, COUNT(*) AS cnt FROM Users GROUP BY Role") or []
    system_stats = {
        "students": count("SELECT COUNT(*) AS c FROM Student"),
        "teachers": count("SELECT COUNT(*) AS c FROM Instructor"),
        "assignments": count("SELECT COUNT(*) AS c FROM Assignment"),
        "pending_regs": count(f"SELECT COUNT(*) AS c FROM ({REGISTRATION_UNION_QUERY}) AS r WHERE Status='Pending'"),
        "notifications": count("SELECT COUNT(*) AS c FROM Notification"),
    }
    return render_template("admin_dashboard.html", pending_regs=pending_regs, user_dist={row["Role"]: row["cnt"] for row in user_dist_rows}, system_stats=system_stats)


@app.route("/admin/registrations")
@admin_required
def registration_review():
    ensure_registration_schema()
    status_filter = request.args.get("status", "").strip()
    type_filter = request.args.get("type", "").strip()
    registrations = query(
        f"""
        SELECT *
        FROM ({REGISTRATION_UNION_QUERY}) AS r
        WHERE (%s='' OR Status=%s)
          AND (%s='' OR Applicant_Type=%s)
        ORDER BY
          CASE Status WHEN 'Pending' THEN 0 WHEN 'Approved' THEN 1 ELSE 2 END,
          Applicant_Type,
          Grade_Applied,
          Submitted_At DESC
        """,
        (status_filter, status_filter, type_filter, type_filter),
    ) or []
    student_registrations = [row for row in registrations if (row.get("Applicant_Type") or "student") == "student"]
    teacher_registrations = [row for row in registrations if (row.get("Applicant_Type") or "student") == "teacher"]
    statuses = ["Pending", "Approved", "Rejected"]
    student_registrations_by_status = {
        status: group_by_year([row for row in student_registrations if row.get("Status") == status], "Grade_Applied")
        for status in statuses
    }
    teacher_registrations_by_status = {
        status: [row for row in teacher_registrations if row.get("Status") == status]
        for status in statuses
    }
    summary = {
        "pending": count(f"SELECT COUNT(*) AS c FROM ({REGISTRATION_UNION_QUERY}) AS r WHERE Status='Pending'"),
        "approved": count(f"SELECT COUNT(*) AS c FROM ({REGISTRATION_UNION_QUERY}) AS r WHERE Status='Approved'"),
        "rejected": count(f"SELECT COUNT(*) AS c FROM ({REGISTRATION_UNION_QUERY}) AS r WHERE Status='Rejected'"),
        "students": count(f"SELECT COUNT(*) AS c FROM ({REGISTRATION_UNION_QUERY}) AS r WHERE Applicant_Type='student'"),
        "teachers": count(f"SELECT COUNT(*) AS c FROM ({REGISTRATION_UNION_QUERY}) AS r WHERE Applicant_Type='teacher'"),
    }
    return render_template(
        "registration_review.html",
        registrations=registrations,
        student_registrations_by_status=student_registrations_by_status,
        teacher_registrations_by_status=teacher_registrations_by_status,
        summary=summary,
        status_filter=status_filter,
        type_filter=type_filter,
    )


@app.route("/admin/registration/<applicant_type>/<int:reg_id>/<action>", methods=["POST"])
@admin_required
def handle_registration(applicant_type, reg_id, action):
    ensure_registration_schema()
    if action not in ("approve", "reject"):
        flash("Unknown registration action.", "danger")
        return redirect(request.referrer or url_for("registration_review"))
        
    if applicant_type == "student":
        registration = query("SELECT * FROM Student_Registration WHERE Student_Reg_ID=%s", (reg_id,), fetchone=True)
        if registration:
            registration["Applicant_Type"] = "student"
    elif applicant_type == "teacher":
        registration = query("SELECT * FROM Teacher_Registration WHERE Teacher_Reg_ID=%s", (reg_id,), fetchone=True)
        if registration:
            registration["Applicant_Type"] = "teacher"
            registration["Email"] = registration.get("Contact_Email")
            registration["Phone"] = registration.get("Phone_Number")
            registration["Employment_Date"] = registration.get("Available_Start_Date")
    else:
        flash("Unknown applicant type.", "danger")
        return redirect(request.referrer or url_for("registration_review"))
            
    if not registration:
        flash("Registration not found.", "danger")
        return redirect(request.referrer or url_for("registration_review"))
    if registration.get("Status") != "Pending":
        flash("This registration was already reviewed.", "info")
        return redirect(request.referrer or url_for("registration_review"))

    applicant_type = (registration.get("Applicant_Type") or "student").lower()
    contact_email = registration_contact_email(registration)
    if not contact_email:
        flash("This registration has no contact email, so it cannot be processed yet.", "danger")
        return redirect(request.referrer or url_for("registration_review"))

    status = "Approved" if action == "approve" else "Rejected"
    if action == "approve":
        if applicant_type == "teacher":
            login_email, temp_password = create_teacher_from_registration(registration)
        else:
            login_email, temp_password = create_student_from_registration(registration)
        if not login_email or not temp_password:
            flash("Could not create the account for this registration. Please check the database settings.", "danger")
            return redirect(request.referrer or url_for("registration_review"))
        email_sent = send_temporary_credentials_email(
            registration.get("Full_Name"),
            contact_email,
            applicant_type,
            temp_password,
            login_email=login_email,
        )
    else:
        email_sent = send_registration_rejection_email(registration.get("Full_Name"), contact_email, applicant_type)

    if applicant_type == "student":
        execute("UPDATE Student_Registration SET Status=%s WHERE Student_Reg_ID=%s", (status, reg_id))
    else:
        execute("UPDATE Teacher_Registration SET Status=%s WHERE Teacher_Reg_ID=%s", (status, reg_id))
    if email_sent:
        flash(f"Registration {status.lower()} and email sent.", "success")
    else:
        flash(f"Registration {status.lower()}, but email delivery failed. Check Mailpit SMTP settings.", "warning")
    return redirect(request.referrer or url_for("registration_review"))


@app.route("/online-registration", methods=["GET", "POST"])
def online_registration():
    ensure_registration_schema()
    if request.method == "POST":
        applicant_type = (request.form.get("applicant_type") or "student").strip().lower()
        if applicant_type not in ("student", "teacher"):
            applicant_type = "student"
        required = ["full_name", "email", "phone"]
        if applicant_type == "student":
            required += ["birth_date", "gender", "nationality", "grade", "parent_name", "parent_phone", "parent_email", "address"]
        else:
            required += ["department", "qualification", "specialization"]
        missing = [field.replace("_", " ").title() for field in required if not request.form.get(field)]
        if missing:
            flash("Please complete: " + ", ".join(missing), "danger")
            return render_template("online_registration.html")
        if applicant_type == "student":
            execute(
                """
                INSERT INTO Student_Registration
                (Full_Name,Birth_Date,Gender,Nationality,Email,Phone,Grade_Applied,Parent_Name,
                 Parent_Phone,Parent_Email,Address,Previous_School,Birth_Certificate,Student_Photo,
                 Previous_Transcript,Notes)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    request.form.get("full_name") or None,
                    request.form.get("birth_date") or None,
                    request.form.get("gender") or None,
                    request.form.get("nationality") or None,
                    request.form.get("email") or None,
                    request.form.get("phone") or None,
                    request.form.get("grade") or None,
                    request.form.get("parent_name") or None,
                    request.form.get("parent_phone") or None,
                    request.form.get("parent_email") or None,
                    request.form.get("address") or None,
                    request.form.get("previous_school") or None,
                    safe_filename("birth_certificate"),
                    safe_filename("student_photo"),
                    safe_filename("previous_transcript"),
                    request.form.get("notes") or None,
                ),
            )
        else:
            execute(
                """
                INSERT INTO Teacher_Registration
                (Full_Name,Contact_Email,Phone_Number,Department,Qualification,Specialization,
                 Available_Start_Date,Address,Notes)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    request.form.get("full_name") or None,
                    request.form.get("email") or None,
                    request.form.get("phone") or None,
                    request.form.get("department") or None,
                    request.form.get("qualification") or None,
                    request.form.get("specialization") or None,
                    request.form.get("employment_date") or None,
                    request.form.get("address") or None,
                    request.form.get("notes") or None,
                ),
            )
        contact_email = request.form.get("email")
        if contact_email:
            send_registration_received_email(request.form.get("full_name"), contact_email)

        flash("Thank you for your registration. We will work on your application and send the decision within 2 days. Please follow your email.", "success")
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
    app.run(debug=True, host="0.0.0.0", port=5001)