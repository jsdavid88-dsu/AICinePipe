@echo off
title AIPipeline Launcher
echo ==========================================
echo    Starting AIPipeline System
echo ==========================================

echo 1. Launching Master Server...
start "AIPipeline - Master Server" cmd /k "python -m master.main"

:: Wait for Master to initialize
timeout /t 3 /nobreak >nul

echo 2. Launching Worker Node...
start "AIPipeline - Worker" cmd /k "python worker/agent.py"

echo 3. Launching Frontend (Vite)...
start "AIPipeline - Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ==========================================
echo    All services launched!
echo    Frontend: http://localhost:5173
echo ==========================================
pause
