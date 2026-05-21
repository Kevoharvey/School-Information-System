# 🏫 Galala International School Information System

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/Flask-Core-green)
![MySQL](https://img.shields.io/badge/MySQL-Database-blue)
![Mailpit](https://img.shields.io/badge/SMTP-Mailpit-orange)
![Status](https://img.shields.io/badge/Status-Completed-success)

---

## 📌 Overview

This project is a professional, database-backed **School Information System** designed for **Galala International School**. It handles registrations, student/teacher accounts, class schedules, assignments, grade submissions, administrative management, analytics, and an integrated AI database query assistant.

### 🍎 Key Portals:
- **Admin Dashboard**: Manage user accounts, verify credentials, approve registrations, and view analytics.
- **Teacher Workspace**: Schedule classes, publish assignments, grade student submissions, and manage subject records.
- **Student Portal**: View personal schedules, download/submit homework, track grades, and receive notices.

### 🎯 Project Goal:
To provide a modern, modular, and secure academic management system that improves communication and automates school administration workflows.

---

## 🚀 Features

- 📑 **Online Registration**: Secure applicant registration with file upload support for school documentation.
- 📬 **Automated Credentials**: Admin-created student/teacher accounts receive temporary passwords via a local SMTP email flow.
- 📊 **Interactive Analytics**: Visual insights on registration trends, grade distributions, and attendance via **Chart.js**.
- 🤖 **AI Query Assistant**: Natural language database query interface with strictly read-only execution guards.
- 📅 **Schedule Visualizer**: Drag-and-drop or clean tabular visualizer for teacher-student timetables.
- 📁 **Modular Codebase**: Clean split of Jinja2 HTML templates, a centralized `static/css/style.css`, and isolated page-specific JavaScript files.

---

## 📂 Frontend Architecture

The user interface follows a highly structured, single-responsibility frontend layout:

```text
templates/
  ├── public_base.html        # Public-facing layout base
  ├── base.html               # Authenticated user layout base
  ├── landing.html            # School homepage
  ├── online_registration.html# New student admission portal
  ├── dashboard.html          # Dynamic dashboards (Student, Teacher, Admin)
  ├── students.html           # Directory of active students
  ├── teachers.html           # Directory of active teachers & subjects
  ├── assignments.html        # Homework creation and grading
  ├── analytics.html          # Performance visualizations
  ├── ai_assistant.html       # AI SQL interface
  ├── Notifications.html      # Central notifications board
  ├── schedule.html           # Timetable calendar
  └── student_profile.html    # Student card and reports
```

- **Styles**: Organized under a unified `static/css/style.css` stylesheet.
- **Scripts**: Page-specific actions are isolated in respective files under `static/js/` (e.g., `landing.js`, `analytics.js`).

---

## 🛠️ Tech Stack

- **Backend**: Flask (Python) 🐍
- **Database**: MySQL 🐬
- **Frontend**: HTML5, Vanilla CSS, JS
- **UI Components**: Bootstrap v5
- **Charts**: Chart.js
- **SMTP**: Mailpit (local testing)

---

## 📌 Prerequisites

Before running the application, make sure you have:

- Python 3.10+
- MySQL Server (3306)
- Mailpit SMTP Server (running locally)
- Git

---

## 📥 Setup Instructions

### 1️⃣ Clone the Repository

```bash
git clone <repository-url>
cd "School-Information-System/School-Information-System"
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Configure Environment Variables

Create a copy of `.env.example` named `.env` and fill in your database credentials:

```bash
cp .env.example .env
```
Default parameters in `.env`:
```ini
DB_HOST=localhost
DB_PORT=3306
DB_NAME=school_db
DB_USER=school_app_user
DB_PASSWORD=strong_password_here
MAILPIT_HOST=localhost
MAILPIT_PORT=1025
```

### 4️⃣ Import Database Schema

Run the database setup script to compile the schema and tables:

```bash
python setup_db.py
```
> [!NOTE]
> The database starts clean without placeholder entities. The **first registered account** on the online registration page will automatically receive the **Admin** role.

### 5️⃣ Run Mailpit & Start Flask

1. Make sure Mailpit is running on `localhost:1025`.
2. Start the development server:

```bash
python app.py
```
Open your browser and navigate to:
```text
http://localhost:5000
```

---

## 💻 Workflow Guidelines

### ⚠️ Important Rules

- **Database Protection**: Never write write-access queries (`INSERT`, `UPDATE`, `DELETE`) inside the AI Assistant code path. The assistant should strictly enforce read-only execution.
- **Securing Credentials**: Do not hardcode database password strings inside `db_config.py` or any repository files. Always read them from `.env` config.
- **Mail Testing**: Always run Mailpit locally while creating student or teacher accounts, so they receive temporary login credentials immediately.

### 🌿 Development Workflow:

1. Retrieve the latest source code before starting features:
   ```bash
   git pull origin main
   ```
2. Make your edits and ensure styling classes follow the centralized `static/css/style.css` rules.
3. Push changes to the repository:
   ```bash
   git add .
   git commit -m "feat: enhance assignment submission file upload"
   git push origin main
   ```

---

## ❤️ Project Vision

Empowering students, teachers, and administrators with premium, responsive, and secure academic tools to foster an efficient and modern learning ecosystem.
