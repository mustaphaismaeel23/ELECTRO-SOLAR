@echo off
title ElectroSolar Manager - Localhost
color 0A
echo.
echo  ==========================================
echo   ElectroSolar Manager - Starting...
echo  ==========================================
echo.
echo  Checking Python...
python --version 2>NUL
if errorlevel 1 (
    echo  ERROR: Python not found!
    echo  Please install Python from https://python.org
    pause
    exit /b 1
)

echo.
echo  Installing/checking dependencies...
pip install -r requirements.txt -q

echo.
echo  Starting server...
echo  Open your browser at: http://localhost:5000
echo  Login: admin / admin123
echo.
echo  Press Ctrl+C to stop the server
echo.
python app.py
pause
