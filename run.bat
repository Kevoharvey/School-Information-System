@echo off
REM Galala International School Portal - Run Script (Windows)

echo ======================================
echo Galala International School Portal
echo ======================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found. Creating one...
    python -m venv venv
    echo Virtual environment created!
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Checking dependencies...
pip install -q -r requirements.txt

echo.
echo Starting Flask application...
echo Access the portal at: http://localhost:5000
echo.
echo Default Login Credentials:
echo   Admin:   admin@galala.edu / admin123
echo   Teacher: teacher@galala.edu / teacher123
echo   Student: student@galala.edu / student123
echo.
echo Press Ctrl+C to stop the server
echo ======================================
echo.

REM Run the Flask app
python app.py

pause
