# Quickstart

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Configure MySQL

Update environment variables if your database credentials are different:

```bash
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=school_db
DB_PORT=3306
```

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

## First Account

Go to `/register` and create the first real account. The first account automatically becomes the admin account.
