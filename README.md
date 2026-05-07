# Galala International School Information System

A Flask-compatible, database-backed school system for Galala International School.

## Frontend Structure

The frontend is refactored into separate HTML, CSS, and JavaScript files:

```text
templates/
  public_base.html
  base.html
  landing.html
  login.html
  register.html
  online_registration.html
  dashboard.html
  students.html
  teachers.html
  assignments.html
  analytics.html
  ai_assistant.html
  Notifications.html
  schedule.html
  admin_dashboard.html
  student_profile.html

static/css/
  style.css

static/js/
  public_base.js
  base.js
  sidebar.js
  landing.js
  login.js
  register.js
  forgot_password.js
  online_registration.js
  dashboard.js
  students.js
  teachers.js
  assignments.js
  analytics.js
  ai_assistant.js
  notifications.js
  schedule.js
  admin_dashboard.js
  student_profile.js
```

All page-specific JavaScript lives in its own file. Shared styling is collected in `static/css/style.css`.

## Main Features

- Modern school landing page
- Online registration with document uploads
- Login, registration, and password reset
- Admin, student, teacher, assignment, analytics, notification, schedule, and AI assistant pages
- MySQL database connection through `db_config.py`
- Chart.js analytics
- AI-generated SQL assistant with read-only query protection

## Setup

```bash
pip install -r requirements.txt
python setup_db.py
python app.py
```

Create the first real account at `/register`; it becomes the admin account automatically.
