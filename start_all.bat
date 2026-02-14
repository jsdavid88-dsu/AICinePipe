@echo off
chcp 65001 >nul
title AIPipeline — All Services
echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║   AIPipeline — Starting All Services         ║
echo  ╚══════════════════════════════════════════════╝
echo.

:: Activate venv if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo  ✅ Virtual environment activated
) else (
    echo  ⚠️  No venv found. Run setup.bat first!
    echo     Or install dependencies manually: pip install -r requirements.txt
    echo.
)

echo.
echo  [1/3] Starting Master Server (port 8002)...
start "AIPipeline — Master Server" cmd /k "title AIPipeline Master & python -m master.main"

:: Wait for Master to initialize
timeout /t 3 /nobreak >nul

echo  [2/3] Starting Worker Node...
start "AIPipeline — Worker" cmd /k "title AIPipeline Worker & python worker/agent.py"

echo  [3/3] Starting Frontend (Vite)...
start "AIPipeline — Frontend" cmd /k "title AIPipeline Frontend & cd frontend && npm run dev"

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║   ✅ All services launched!                  ║
echo  ║                                              ║
echo  ║   Frontend:  http://localhost:5173            ║
echo  ║   API Docs:  http://localhost:8002/docs       ║
echo  ║                                              ║
echo  ║   Close this window to keep running,         ║
echo  ║   or close each service window to stop it.   ║
echo  ╚══════════════════════════════════════════════╝
echo.
pause
