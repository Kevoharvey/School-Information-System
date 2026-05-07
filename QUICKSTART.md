# Quick Start Guide - Galala International School Portal

## 🚀 Get Started in 3 Minutes

### Option 1: Quick Start (Recommended)

**On Linux/Mac:**
```bash
cd galala_school_portal
chmod +x run.sh
./run.sh
```

**On Windows:**
```bash
cd galala_school_portal
run.bat
```

The script will automatically:
- Create a virtual environment
- Install all dependencies
- Start the Flask server
- Open on http://localhost:5000

### Option 2: Manual Setup

1. **Navigate to project folder**
   ```bash
   cd galala_school_portal
   ```

2. **Create virtual environment** (optional but recommended)
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
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

5. **Open your browser**
   ```
   http://localhost:5000
   ```

## 🔑 Test Accounts

### Administrator
- **Email**: admin@galala.edu
- **Password**: admin123
- **Features**: Full access to all features including admin dashboard

### Teacher
- **Email**: teacher@galala.edu
- **Password**: teacher123
- **Features**: Access to teaching tools and student management

### Student
- **Email**: student@galala.edu
- **Password**: student123
- **Features**: Access to personal dashboard and assignments

## 📱 What You'll See

After logging in, you'll have access to:

- **Dashboard** - Overview of school activities
- **Students** - Student management and profiles
- **Teachers** - Faculty information and management
- **Assignments** - Create and track assignments
- **Analytics** - Performance metrics and insights
- **AI Assistant** - Intelligent academic support
- **Schedule** - Class schedules and timetables
- **Notifications** - Important announcements
- **Admin Panel** - Administrative controls (admin only)

## 🛠️ Troubleshooting

### "Port 5000 already in use"
Change the port in `app.py` line 158:
```python
app.run(debug=True, host='0.0.0.0', port=5001)
```

### "Module not found: Flask"
Make sure you've installed the dependencies:
```bash
pip install -r requirements.txt
```

### Static files not loading
Clear your browser cache (Ctrl+Shift+R or Cmd+Shift+R)

## 📞 Need Help?

1. Check the full README.md for detailed documentation
2. Verify all files are in the correct directories
3. Make sure Python 3.8+ is installed
4. Try running in a fresh virtual environment

## 🎯 Next Steps

1. **Customize**: Edit colors and branding in `static/css/style.css`
2. **Add Database**: Integrate SQLAlchemy for real data storage
3. **Deploy**: Use Gunicorn + Nginx for production
4. **Secure**: Change the secret key in `app.py`

---

**Ready to go!** Start with the admin account to explore all features.

✨ Built with Flask, Tailwind CSS, and modern web standards.
