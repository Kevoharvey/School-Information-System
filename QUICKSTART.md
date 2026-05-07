# Quickstart

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Configure MySQL

Update environment variables if your database credentials are different:

```bash
DB_HOST=localhost
DB_USER=school_app_user
DB_PASSWORD=strong_password_here
DB_NAME=school_db
DB_PORT=3306
```

Do not hardcode credentials in source files. Keep real values in your local environment (or `.env`, which is gitignored).

## 3. Import Database

```bash
python setup_db.py
```

The schema starts without placeholder students, teachers, assignments, grades, schedules, notifications, or registrations.

## 4. Start Flask

```bash
python app.py
```

Open:

```text
http://localhost:5000
```

## Mailpit for Temporary Credentials

Run Mailpit SMTP locally on `localhost:1025` (or set `MAILPIT_HOST` and `MAILPIT_PORT`) so admin-created student and teacher accounts receive temporary login credentials by email.
