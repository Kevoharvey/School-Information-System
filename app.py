from flask import Flask, send_from_directory, request, jsonify, session
import mysql.connector
import os

app = Flask(__name__, static_folder="static")
app.secret_key = "school_is_secret_key_2026"


# ── DB CONNECTION ─────────────────────────────────────────────
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="school_db",
        port=3306
    )


def db_query(sql, params=(), fetchone=False, commit=False):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(sql, params)
    result = None
    if commit:
        db.commit()
    elif fetchone:
        result = cursor.fetchone()
    else:
        result = cursor.fetchall()
    db.close()
    return result


# =============================================================
#  SERVE FRONTEND
# =============================================================
@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)


# =============================================================
#  AUTH
# =============================================================
@app.route("/api/signin", methods=["POST"])
def api_signin():
    data = request.get_json()
    role = data.get("role")
    id_  = data.get("id")
    password = data.get("password")

    if not id_ or not password or len(str(password)) < 4:
        return jsonify({"ok": False, "error": "Invalid credentials"}), 400

    try:
        id_int = int(id_)
    except ValueError:
        return jsonify({"ok": False, "error": "ID must be numeric"}), 400

    if role == "student":
        row = db_query(
            "SELECT Student_ID, Fname, Lname FROM Student WHERE Student_ID = %s",
            (id_int,), fetchone=True
        )
        if not row:
            return jsonify({"ok": False, "error": "Student not found"}), 404
        session["user"] = {"id": row["Student_ID"], "name": f"{row['Fname']} {row['Lname']}", "role": "student"}
    else:
        row = db_query(
            """SELECT e.Emp_ID, e.Emp_FName, e.Emp_Lname FROM Employee e
               JOIN Instructor i ON e.Emp_ID = i.Emp_ID WHERE e.Emp_ID = %s""",
            (id_int,), fetchone=True
        )
        if not row:
            return jsonify({"ok": False, "error": "Instructor not found"}), 404
        session["user"] = {"id": row["Emp_ID"], "name": f"{row['Emp_FName']} {row['Emp_Lname']}", "role": "teacher"}

    return jsonify({"ok": True, "user": session["user"]})


@app.route("/api/signup", methods=["POST"])
def api_signup():
    data = request.get_json()
    role     = data.get("role")
    name     = data.get("name", "").strip()
    email    = data.get("email", "").strip()
    id_      = data.get("id", "").strip()
    password = data.get("password", "")

    if not all([name, email, id_, password]) or len(password) < 6:
        return jsonify({"ok": False, "error": "All fields required; password >= 6 chars"}), 400

    try:
        id_int = int(id_)
    except ValueError:
        return jsonify({"ok": False, "error": "ID must be numeric"}), 400

    parts = name.strip().split(" ", 1)
    fname = parts[0]
    lname = parts[1] if len(parts) > 1 else ""

    try:
        if role == "student":
            db_query(
                "INSERT INTO Student (Student_ID, Fname, Lname, Student_Email) VALUES (%s, %s, %s, %s)",
                (id_int, fname, lname, email), commit=True
            )
        else:
            dept = db_query("SELECT Dept_ID FROM Department ORDER BY Dept_ID LIMIT 1", fetchone=True)
            if not dept:
                return jsonify({"ok": False, "error": "No departments exist yet"}), 400
            db_query(
                "INSERT INTO Employee (Emp_ID, Emp_FName, Emp_Lname, Dept_ID) VALUES (%s, %s, %s, %s)",
                (id_int, fname, lname, dept["Dept_ID"]), commit=True
            )
            db_query("INSERT INTO Instructor (Emp_ID) VALUES (%s)", (id_int,), commit=True)
        session["user"] = {"id": id_int, "name": name, "role": role}
    except mysql.connector.IntegrityError:
        return jsonify({"ok": False, "error": "That ID is already taken"}), 409

    return jsonify({"ok": True, "user": session["user"]})


@app.route("/api/signout", methods=["POST"])
def api_signout():
    session.clear()
    return jsonify({"ok": True})


@app.route("/api/me")
def api_me():
    user = session.get("user")
    if not user:
        return jsonify({"ok": False}), 401
    return jsonify({"ok": True, "user": user})


# =============================================================
#  DASHBOARD STATS
# =============================================================
@app.route("/api/stats")
def api_stats():
    tables = ["Student", "Instructor", "Subject", "Department", "Classroom"]
    stats = {}
    for t in tables:
        row = db_query(f"SELECT COUNT(*) AS c FROM {t}", fetchone=True)
        stats[t.lower() + "s"] = row["c"]
    recent = db_query("SELECT Student_ID, Fname, Lname, Level FROM Student ORDER BY Student_ID DESC LIMIT 5")
    return jsonify({"ok": True, "stats": stats, "recent_students": recent})


# =============================================================
#  STUDENTS
# =============================================================
@app.route("/api/students", methods=["GET"])
def api_students_list():
    rows = db_query("SELECT * FROM Student ORDER BY Student_ID")
    for r in rows:
        if r.get("Birth_Date"):
            r["Birth_Date"] = str(r["Birth_Date"])
    return jsonify({"ok": True, "students": rows})


@app.route("/api/students", methods=["POST"])
def api_students_add():
    d = request.get_json()
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


@app.route("/api/students/<int:student_id>", methods=["PUT"])
def api_students_edit(student_id):
    d = request.get_json()
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


@app.route("/api/students/<int:student_id>", methods=["DELETE"])
def api_students_delete(student_id):
    db_query("DELETE FROM Student WHERE Student_ID = %s", (student_id,), commit=True)
    return jsonify({"ok": True, "message": "Student deleted."})


@app.route("/api/students/<int:student_id>/grades")
def api_student_grades(student_id):
    rows = db_query(
        """SELECT s.Subject_Name, st.Grades
           FROM Studies st JOIN Subject s ON st.Subject_ID = s.Subject_ID
           WHERE st.Student_ID = %s""",
        (student_id,)
    )
    return jsonify({"ok": True, "grades": rows})


# =============================================================
#  GRADES (Studies)
# =============================================================
@app.route("/api/grades", methods=["POST"])
def api_grades_upsert():
    d = request.get_json()
    db_query(
        """INSERT INTO Studies (Student_ID, Subject_ID, Grades)
           VALUES (%s, %s, %s)
           ON DUPLICATE KEY UPDATE Grades = %s""",
        (d["student_id"], d["subject_id"], d["grade"], d["grade"]),
        commit=True
    )
    return jsonify({"ok": True, "message": "Grade saved!"})


# =============================================================
#  INSTRUCTORS
# =============================================================
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


@app.route("/api/instructors", methods=["POST"])
def api_instructors_add():
    d = request.get_json()
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


@app.route("/api/instructors/<int:emp_id>", methods=["DELETE"])
def api_instructors_delete(emp_id):
    db_query("DELETE FROM Employee WHERE Emp_ID = %s", (emp_id,), commit=True)
    return jsonify({"ok": True, "message": "Instructor deleted."})


# =============================================================
#  EMPLOYEES
# =============================================================
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


@app.route("/api/employees", methods=["POST"])
def api_employees_add():
    d = request.get_json()
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


@app.route("/api/employees/<int:emp_id>", methods=["DELETE"])
def api_employees_delete(emp_id):
    db_query("DELETE FROM Employee WHERE Emp_ID = %s", (emp_id,), commit=True)
    return jsonify({"ok": True, "message": "Employee deleted."})


# =============================================================
#  SUBJECTS
# =============================================================
@app.route("/api/subjects", methods=["GET"])
def api_subjects_list():
    rows = db_query("""
        SELECT s.*, c.Classroom_Building, c.Classroom_Floor
        FROM Subject s
        LEFT JOIN Classroom c ON s.Classroom_ID = c.Classroom_ID
        ORDER BY s.Subject_ID
    """)
    return jsonify({"ok": True, "subjects": rows})


@app.route("/api/subjects", methods=["POST"])
def api_subjects_add():
    d = request.get_json()
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


@app.route("/api/subjects/<int:subject_id>", methods=["DELETE"])
def api_subjects_delete(subject_id):
    db_query("DELETE FROM Subject WHERE Subject_ID = %s", (subject_id,), commit=True)
    return jsonify({"ok": True, "message": "Subject deleted."})


# =============================================================
#  CLASSROOMS
# =============================================================
@app.route("/api/classrooms", methods=["GET"])
def api_classrooms_list():
    rows = db_query("SELECT * FROM Classroom ORDER BY Classroom_ID")
    return jsonify({"ok": True, "classrooms": rows})


@app.route("/api/classrooms", methods=["POST"])
def api_classrooms_add():
    d = request.get_json()
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


@app.route("/api/classrooms/<int:classroom_id>", methods=["DELETE"])
def api_classrooms_delete(classroom_id):
    db_query("DELETE FROM Classroom WHERE Classroom_ID = %s", (classroom_id,), commit=True)
    return jsonify({"ok": True, "message": "Classroom deleted."})


# =============================================================
#  DEPARTMENTS
# =============================================================
@app.route("/api/departments", methods=["GET"])
def api_departments_list():
    rows = db_query("SELECT * FROM Department ORDER BY Dept_ID")
    return jsonify({"ok": True, "departments": rows})


@app.route("/api/departments", methods=["POST"])
def api_departments_add():
    d = request.get_json()
    try:
        db_query(
            "INSERT INTO Department (Dept_ID, Dept_Name, Dept_Head) VALUES (%s, %s, %s)",
            (d["dept_id"], d["dept_name"], d.get("dept_head") or None),
            commit=True
        )
    except mysql.connector.IntegrityError as e:
        return jsonify({"ok": False, "error": str(e)}), 409
    return jsonify({"ok": True, "message": "Department added!"})


@app.route("/api/departments/<int:dept_id>", methods=["DELETE"])
def api_departments_delete(dept_id):
    db_query("DELETE FROM Department WHERE Dept_ID = %s", (dept_id,), commit=True)
    return jsonify({"ok": True, "message": "Department deleted."})


# =============================================================
#  TEACHER — subjects + students
# =============================================================
@app.route("/api/teacher/<int:emp_id>/subjects")
def api_teacher_subjects(emp_id):
    rows = db_query(
        """SELECT s.Subject_ID, s.Subject_Name, s.Subject_Level, s.Subject_Slots
           FROM Teaches t JOIN Subject s ON t.Subject_ID = s.Subject_ID
           WHERE t.Emp_ID = %s""",
        (emp_id,)
    )
    return jsonify({"ok": True, "subjects": rows})


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


# =============================================================
#  RUN
# =============================================================
if __name__ == "__main__":
    app.run(debug=True)
