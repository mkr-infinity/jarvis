@echo off
REM JARVIS Quick Start Script for Windows
REM Usage: run.bat

echo JARVIS Starting...

REM Kill any existing JARVIS processes
echo Cleaning up...
taskkill /F /IM python.exe 2>nul
timeout /t 1 /nobreak >nul

REM Create virtual environment if not exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
echo Activating environment...
call .venv\Scripts\activate.bat

REM Install dependencies if needed
if not exist ".venv\Lib\site-packages\fastapi" (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Start backend
echo Starting backend...
start /b python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8765

REM Wait for backend to start
timeout /t 3 /nobreak >nul

REM Check backend health
curl -s http://127.0.0.1:8765/health >nul 2>&1
if %errorlevel% equ 0 (
    echo Backend running on http://127.0.0.1:8765
) else (
    echo Backend failed to start
    exit /b 1
)

REM Start Electron
echo Starting JARVIS GUI...
npx electron .

REM Cleanup on exit
echo Cleaning up...
call .venv\Scripts\deactivate.bat 2>nul
echo Goodbye!
pause