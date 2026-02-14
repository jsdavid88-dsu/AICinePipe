#!/usr/bin/env bash
set -e

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   AIPipeline Tool — One-Click Setup          ║"
echo "║   AI Production Pipeline for ComfyUI         ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── Check Python ──────────────────────────────────────────
echo "[1/5] Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "  ❌ Python 3 not found! Install Python 3.10+:"
    echo "     Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip"
    echo "     macOS: brew install python3"
    exit 1
fi
PYVER=$(python3 --version 2>&1)
echo "  ✅ $PYVER found"

# ── Check Node.js ─────────────────────────────────────────
echo "[2/5] Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo "  ❌ Node.js not found! Install Node.js 18+:"
    echo "     https://nodejs.org or: brew install node"
    exit 1
fi
NODEVER=$(node --version 2>&1)
echo "  ✅ Node.js $NODEVER found"

# ── Create venv & install Python deps ─────────────────────
echo ""
echo "[3/5] Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "  ✅ Virtual environment created"
else
    echo "  ✅ Virtual environment already exists"
fi

source venv/bin/activate
echo "  📦 Installing Python dependencies..."
pip install -r requirements.txt --quiet --disable-pip-version-check
echo "  ✅ Python dependencies installed"

# ── Install frontend deps ─────────────────────────────────
echo ""
echo "[4/5] Setting up Frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "  📦 Installing npm packages (this may take a minute)..."
    npm install --silent 2>/dev/null || true
    echo "  ✅ Frontend dependencies installed"
else
    echo "  ✅ Frontend dependencies already installed"
fi
cd ..

# ── Create .env if missing ────────────────────────────────
echo ""
echo "[5/5] Checking configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "  ✅ Created .env from .env.example"
    echo "  💡 Edit .env to set your ComfyUI URL, LLM API keys, etc."
else
    echo "  ✅ .env already exists"
fi

# ── Create data directories ───────────────────────────────
mkdir -p data projects logs

# ── Done! ─────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   ✅ Setup Complete!                         ║"
echo "║                                              ║"
echo "║   To start the system:                       ║"
echo "║     python launcher.py                       ║"
echo "║                                              ║"
echo "║   Frontend: http://localhost:5173             ║"
echo "║   API Docs: http://localhost:8002/docs        ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
