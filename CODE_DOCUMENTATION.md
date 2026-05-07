# Code Documentation

## Architecture

The app follows a Flask-compatible structure:

```text
app.py
db_config.py
db.sql
templates/
static/css/style.css
static/js/
static/uploads/
```

## Frontend Rules

- Templates contain markup only.
- Shared styling lives in `static/css/style.css`.
- Each full template has a matching page JavaScript file in `static/js/`.
- Shared layout behavior lives in `public_base.js`, `base.js`, and `sidebar.js`.
- Bootstrap is used for layout and components.
- Chart.js is used on the analytics page.

## Data Rules

- Operational tables start empty.
- Real students, teachers, assignments, schedules, registrations, notifications, and grades are added through the app.
- The first registered account becomes the admin account.

## Security Notes

- Passwords are hashed with Flask-Bcrypt.
- The AI assistant only runs SELECT queries.
- File uploads are saved with secure generated filenames under `static/uploads/`.
