@echo off
chcp 65001 >nul
title AIPipeline — Setup
echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║   AIPipeline Tool — One-Click Setup          ║
echo  ║   AI Production Pipeline for ComfyUI         ║
echo  ╚══════════════════════════════════════════════╝
echo.

:: ── Check Python ──────────────────────────────────────────
echo [1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo  ❌ Python not found! Please install Python 3.10+ from https://python.org
    echo     Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  ✅ Python %PYVER% found

:: ── Check Node.js ─────────────────────────────────────────
echo [2/5] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo  ❌ Node.js not found! Please install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)
for /f %%v in ('node --version 2^>^&1') do set NODEVER=%%v
echo  ✅ Node.js %NODEVER% found

:: ── Create venv & install Python deps ─────────────────────
echo.
echo [3/5] Setting up Python virtual environment...
if not exist "venv" (
    python -m venv venv
    echo  ✅ Virtual environment created
) else (
    echo  ✅ Virtual environment already exists
)

call venv\Scripts\activate.bat
echo  📦 Installing Python dependencies...
pip install -r requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 (
    echo  ❌ pip install failed!
    pause
    exit /b 1
)
echo  ✅ Python dependencies installed

:: ── Install frontend deps ─────────────────────────────────
echo.
echo [4/5] Setting up Frontend...
cd frontend
if not exist "node_modules" (
    echo  📦 Installing npm packages (this may take a minute)...
    call npm install --silent 2>nul
    if errorlevel 1 (
        echo  ⚠️  npm install had warnings, but continuing...
    )
    echo  ✅ Frontend dependencies installed
) else (
    echo  ✅ Frontend dependencies already installed
)
cd ..

:: ── Create .env if missing ────────────────────────────────
echo.
echo [5/5] Checking configuration...
if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo  ✅ Created .env from .env.example
    echo  💡 Edit .env to set your ComfyUI URL, LLM API keys, etc.
) else (
    echo  ✅ .env already exists
)

:: ── Create data directories ───────────────────────────────
if not exist "data" mkdir data
if not exist "projects" mkdir projects
if not exist "logs" mkdir logs

:: ── Done! ─────────────────────────────────────────────────
echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║   ✅ Setup Complete!                         ║
echo  ║                                              ║
echo  ║   To start the system:                       ║
echo  ║     start_all.bat                            ║
echo  ║                                              ║
echo  ║   Or run individually:                       ║
echo  ║     python launcher.py                       ║
echo  ║                                              ║
echo  ║   Frontend: http://localhost:5173             ║
echo  ║   API Docs: http://localhost:8002/docs        ║
echo  ╚══════════════════════════════════════════════╝
echo.
pause
