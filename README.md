# Galala International School Portal

A comprehensive school management system built with Flask and modern web technologies.

## Features

- 🔐 **Authentication System** - Secure login with role-based access control
- 👨‍🎓 **Student Management** - Track student profiles, enrollments, and performance
- 👨‍🏫 **Teacher Management** - Manage faculty information and assignments
- 📊 **Analytics Dashboard** - Visual insights into school performance
- 📝 **Assignment Tracking** - Create and monitor student assignments
- 🤖 **AI Assistant** - Intelligent support for academic queries
- 📅 **Schedule Management** - Class schedules and timetables
- 🔔 **Notifications** - Stay updated with important announcements
- 👤 **User Profiles** - Detailed student and teacher profiles
- 🛡️ **Admin Dashboard** - Comprehensive administrative controls

## Technology Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML5, Tailwind CSS
- **Icons**: Material Symbols
- **Fonts**: Poppins, Inter

## Project Structure

```
galala_school_portal/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── static/
│   ├── css/
│   │   └── style.css          # Custom styles and design system
│   └── js/
│       └── tailwind.config.js # Tailwind configuration
└── templates/
    ├── login.html             # Login page
    ├── landing.html           # Landing/home page
    ├── dashboard.html         # Main dashboard
    ├── students.html          # Student management
    ├── student_profile.html   # Individual student profile
    ├── teachers.html          # Teacher management
    ├── assignments.html       # Assignment tracking
    ├── analytics.html         # Analytics dashboard
    ├── ai_assistant.html      # AI assistant interface
    ├── schedule.html          # Schedule management
    ├── Notifications.html     # Notifications center
    ├── admin_dashboard.html   # Admin-only dashboard
    ├── online_registration.html # Public registration
    └── sidebar.html           # Sidebar navigation component
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup Steps

1. **Clone or download the project**
   ```bash
   cd galala_school_portal
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # Activate on Windows
   venv\Scripts\activate
   
   # Activate on macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   Open your web browser and navigate to:
   ```
   http://localhost:5000
   ```

## Default Login Credentials

### Admin Account
- **Email**: `admin@galala.edu`
- **Password**: `admin123`
- **Access**: Full system access including admin dashboard

### Teacher Account
- **Email**: `teacher@galala.edu`
- **Password**: `teacher123`
- **Access**: Teacher-specific features

### Student Account
- **Email**: `student@galala.edu`
- **Password**: `student123`
- **Access**: Student-specific features

⚠️ **Important**: Change these credentials in production!

## Available Routes

| Route | Description | Access |
|-------|-------------|--------|
| `/` | Landing page | Public |
| `/login` | Login page | Public |
| `/logout` | Logout | Authenticated |
| `/dashboard` | Main dashboard | Authenticated |
| `/students` | Student management | Authenticated |
| `/student-profile` | Student profile | Authenticated |
| `/teachers` | Teacher management | Authenticated |
| `/assignments` | Assignments | Authenticated |
| `/analytics` | Analytics dashboard | Authenticated |
| `/ai-assistant` | AI assistant | Authenticated |
| `/schedule` | Schedule | Authenticated |
| `/notifications` | Notifications | Authenticated |
| `/admin-dashboard` | Admin panel | Admin only |
| `/online-registration` | Public registration | Public |

## Configuration

### Secret Key
For production, change the secret key in `app.py`:
```python
app.secret_key = 'your-secure-random-secret-key-here'
```

Generate a secure secret key:
```python
import secrets
print(secrets.token_hex(32))
```

### Database Integration
The current implementation uses a mock user database. For production:

1. Install a database adapter (e.g., Flask-SQLAlchemy)
2. Create database models
3. Update authentication logic
4. Migrate user data

## Development

### Running in Debug Mode
The application runs in debug mode by default during development:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

### Production Deployment
For production deployment:

1. Set `debug=False`
2. Use a production WSGI server (e.g., Gunicorn, uWSGI)
3. Set up a reverse proxy (e.g., Nginx)
4. Use environment variables for configuration
5. Implement proper database
6. Add SSL/TLS encryption
7. Set up logging and monitoring

Example with Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Features Overview

### Authentication & Authorization
- Session-based authentication
- Role-based access control (Admin, Teacher, Student)
- Login required decorators
- Secure password handling

### User Interface
- Modern, responsive design
- Tailwind CSS for styling
- Material Symbols icons
- Custom design system with consistent colors and typography
- Mobile-friendly navigation

### Design System
The application uses a comprehensive design system with:
- Color palette (Primary, Secondary, Tertiary)
- Typography scale (H1-H3, Body, Caption, Labels)
- Spacing scale (Stack, Gutter, Container margins)
- Component styles (Cards, Buttons, Forms)

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Troubleshooting

### Port Already in Use
If port 5000 is already in use, change the port in `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)
```

### Static Files Not Loading
Ensure the file paths in templates match the Flask static folder structure:
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}" />
```

### Template Not Found
Verify all HTML files are in the `templates/` directory.

## License

Copyright © 2024 Galala International School. All Rights Reserved.

## Support

For support and questions, contact the development team or visit the support center within the application.

---

**Note**: This is a demonstration application. For production use, implement:
- Real database integration
- Enhanced security measures
- Email verification
- Password reset functionality
- File upload capabilities
- API integrations
- Comprehensive testing
- Backup and recovery procedures
