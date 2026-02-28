@echo off
echo.
echo  ApplyAI SaaS — Starting...
echo ======================================

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install from https://python.org
    pause
    exit /b 1
)

:: Install dependencies
echo [INFO] Installing backend packages...
cd backend
pip install -r requirements.txt -q

:: Start backend
echo [INFO] Starting backend on http://localhost:8000 ...
start "ApplyAI Backend" python main.py

:: Wait for backend
timeout /t 3 /nobreak >nul

cd ..

:: Open frontend
echo [INFO] Opening dashboard...
start "" frontend\index.html

echo.
echo ======================================
echo  ApplyAI is running!
echo  Dashboard : Open frontend\index.html
echo  API Docs  : http://localhost:8000/docs
echo  Extension : Load extension\ in Chrome
echo ======================================
echo.
pause
