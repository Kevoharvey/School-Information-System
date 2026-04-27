from flask import Flask, render_template
import mysql.connector

app = Flask(__name__)

# DB CONNECTION
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="password",
        database="school_db"
        port="3306"
    )

# =========================
# ROUTES
# =========================

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/students")
def students():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM Student")
    students = cursor.fetchall()

    db.close()
    return render_template("students.html", students=students)


# RUN APP
if __name__ == "__main__":
    app.run(debug=True)