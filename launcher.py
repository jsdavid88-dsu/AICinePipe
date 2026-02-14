"""
AIPipeline Unified Launcher
============================
Starts all services in the correct order with health checks:
  1. ComfyUI (if COMFYUI_AUTO_START=true and comfyui/ exists)
  2. Master Server (FastAPI)
  3. Worker Agent (connects to Master, talks to ComfyUI)
  4. Frontend Dev Server (only if dist/ doesn't exist)

Usage:
    python launcher.py              # Start everything
    python launcher.py --no-comfy   # Skip ComfyUI
    python launcher.py --no-worker  # Skip Worker
    python launcher.py --build      # Build frontend first, then start
"""

import subprocess
import time
import os
import sys
import argparse
import signal
from pathlib import Path
from threading import Thread

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Configuration ───────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent

# ComfyUI
COMFYUI_DIR = Path(os.getenv("COMFYUI_DIR", str(PROJECT_ROOT / "comfyui")))
COMFYUI_URL = os.getenv("COMFYUI_URL", "http://127.0.0.1:8188")
COMFYUI_AUTO_START = os.getenv("COMFYUI_AUTO_START", "true").lower() == "true"
COMFYUI_MAIN = COMFYUI_DIR / "main.py"

# Master
MASTER_CMD = [sys.executable, "-m", "master.main"]
MASTER_PORT = int(os.getenv("MASTER_PORT", "8002"))

# Worker
WORKER_CMD = [sys.executable, "worker/agent.py"]

# Frontend
FRONTEND_DIR = PROJECT_ROOT / "frontend"
FRONTEND_DIST = FRONTEND_DIR / "dist"
FRONTEND_CMD = ["npm", "run", "dev"]

# Health check
HEALTH_TIMEOUT = 30  # seconds to wait for service readiness
HEALTH_INTERVAL = 1  # seconds between checks

# ── Process Management ──────────────────────────────────────────────────

processes = {}


def stream_reader(pipe, prefix):
    """Read subprocess output line by line and print with prefix."""
    try:
        with pipe:
            for line in iter(pipe.readline, ''):
                stripped = line.strip()
                if stripped:
                    print(f"  [{prefix}] {stripped}")
    except (ValueError, OSError):
        pass


def start_process(name, cmd, cwd=None):
    """Start a subprocess with output streaming."""
    try:
        is_shell = (name == "frontend" and os.name == 'nt')

        p = subprocess.Popen(
            cmd,
            cwd=str(cwd) if cwd else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            shell=is_shell,
        )

        Thread(target=stream_reader, args=(p.stdout, name.upper()), daemon=True).start()
        Thread(target=stream_reader, args=(p.stderr, f"{name.upper()} ERR"), daemon=True).start()

        processes[name] = p
        return p
    except Exception as e:
        print(f"  ❌ Failed to start {name}: {e}")
        return None


def wait_for_http(url, name, timeout=HEALTH_TIMEOUT):
    """Wait until an HTTP service responds."""
    import urllib.request
    import urllib.error

    print(f"  ⏳ Waiting for {name} ({url})...", end="", flush=True)
    elapsed = 0
    while elapsed < timeout:
        try:
            urllib.request.urlopen(url, timeout=2)
            print(f" ✅ ready ({elapsed}s)")
            return True
        except (urllib.error.URLError, OSError, ConnectionError):
            time.sleep(HEALTH_INTERVAL)
            elapsed += HEALTH_INTERVAL
            print(".", end="", flush=True)

    print(f" ❌ timeout after {timeout}s")
    return False


def kill_process_tree(name):
    """Kill a process and all its children."""
    p = processes.get(name)
    if not p or p.poll() is not None:
        return

    if HAS_PSUTIL:
        try:
            parent = psutil.Process(p.pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
        except psutil.NoSuchProcess:
            pass
    else:
        p.kill()


def shutdown_all():
    """Gracefully stop all services in reverse order."""
    order = ["frontend", "worker", "master", "comfyui"]
    for name in order:
        if name in processes:
            p = processes[name]
            if p.poll() is None:
                print(f"  Stopping {name} (PID {p.pid})...")
                kill_process_tree(name)


# ── Main Flow ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AIPipeline Unified Launcher")
    parser.add_argument("--no-comfy", action="store_true", help="Skip ComfyUI auto-start")
    parser.add_argument("--no-worker", action="store_true", help="Skip Worker start")
    parser.add_argument("--no-frontend", action="store_true", help="Skip Frontend dev server")
    parser.add_argument("--build", action="store_true", help="Build frontend before starting")
    args = parser.parse_args()

    print()
    print("╔══════════════════════════════════════════════╗")
    print("║   🚀 AIPipeline Unified Launcher             ║")
    print("╚══════════════════════════════════════════════╝")
    print()

    # ── Step 0: Build frontend if requested ─────────────────────────
    if args.build:
        print("[0/4] Building frontend...")
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=str(FRONTEND_DIR),
            shell=(os.name == 'nt'),
        )
        if result.returncode == 0:
            print("  ✅ Frontend built to dist/")
        else:
            print("  ❌ Frontend build failed!")
            return

    # ── Step 1: ComfyUI ─────────────────────────────────────────────
    start_comfy = (
        COMFYUI_AUTO_START
        and not args.no_comfy
        and COMFYUI_MAIN.exists()
    )

    if start_comfy:
        print("[1/4] Starting ComfyUI...")
        comfy_cmd = [sys.executable, str(COMFYUI_MAIN)]

        # Detect GPU and add appropriate flags
        comfy_cmd.extend(["--listen", "127.0.0.1", "--port", "8188"])

        start_process("comfyui", comfy_cmd, cwd=COMFYUI_DIR)

        if not wait_for_http(f"{COMFYUI_URL}/system_stats", "ComfyUI"):
            print("  ⚠️  ComfyUI not ready. Worker may fail to connect.")
    elif COMFYUI_MAIN.exists() and args.no_comfy:
        print("[1/4] ComfyUI: skipped (--no-comfy)")
    else:
        print("[1/4] ComfyUI: not found in comfyui/ — assuming external")
        print(f"  💡 Set COMFYUI_URL in .env (current: {COMFYUI_URL})")

    # ── Step 2: Master Server ───────────────────────────────────────
    print(f"[2/4] Starting Master Server (port {MASTER_PORT})...")
    start_process("master", MASTER_CMD, cwd=PROJECT_ROOT)

    if not wait_for_http(f"http://127.0.0.1:{MASTER_PORT}/docs", "Master"):
        print("  ❌ Master failed to start. Aborting.")
        shutdown_all()
        return

    # ── Step 3: Worker ──────────────────────────────────────────────
    if not args.no_worker:
        print("[3/4] Starting Worker...")
        start_process("worker", WORKER_CMD, cwd=PROJECT_ROOT)
        time.sleep(1)
        w = processes.get("worker")
        if w and w.poll() is None:
            print("  ✅ Worker started")
        else:
            print("  ⚠️  Worker may have failed to start")
    else:
        print("[3/4] Worker: skipped (--no-worker)")

    # ── Step 4: Frontend ────────────────────────────────────────────
    has_dist = FRONTEND_DIST.exists() and (FRONTEND_DIST / "index.html").exists()

    if has_dist:
        print("[4/4] Frontend: serving from built dist/ via Master")
        print(f"  🌐 Open http://localhost:{MASTER_PORT}")
    elif not args.no_frontend:
        print("[4/4] Starting Frontend dev server...")
        start_process("frontend", FRONTEND_CMD, cwd=FRONTEND_DIR)
        time.sleep(2)
        print("  🌐 Open http://localhost:5173")
    else:
        print("[4/4] Frontend: skipped")

    # ── Ready ───────────────────────────────────────────────────────
    print()
    print("╔══════════════════════════════════════════════╗")
    print("║   ✅ All services running!                   ║")
    print("║                                              ║")
    if has_dist:
        print(f"║   UI:       http://localhost:{MASTER_PORT}             ║")
    else:
        print("║   UI:       http://localhost:5173            ║")
    print(f"║   API Docs: http://localhost:{MASTER_PORT}/docs        ║")
    print("║                                              ║")
    print("║   Press Ctrl+C to stop all services.         ║")
    print("╚══════════════════════════════════════════════╝")
    print()

    # ── Keep alive ──────────────────────────────────────────────────
    try:
        while True:
            time.sleep(2)
            # Check if master is still alive
            master = processes.get("master")
            if master and master.poll() is not None:
                print("\n  ❌ Master Server died! Shutting down...")
                break
    except KeyboardInterrupt:
        print("\n\n  🛑 Shutting down all services...")
    finally:
        shutdown_all()
        print("  👋 Goodbye!")


if __name__ == "__main__":
    main()
