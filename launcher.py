import subprocess
import time
import os
import sys
import psutil
from threading import Thread

# Configuration
MASTER_CMD = [sys.executable, "-m", "master.main"]
WORKER_CMD = [sys.executable, "worker/agent.py"]
FRONTEND_CMD = ["npm", "run", "dev"]
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")

processes = []

def stream_reader(pipe, prefix):
    try:
        with pipe:
            for line in iter(pipe.readline, ''):
                print(f"[{prefix}] {line.strip()}")
    except ValueError:
        pass

def start_process(cmd, cwd=None, prefix="PROC"):
    try:
        # shell=True for npm on Windows to resolve PATH correctly
        is_shell = (prefix == "FRONTEND" and os.name == 'nt')
        
        p = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            shell=is_shell
        )
        
        # Start threads to read stdout/stderr non-blocking
        Thread(target=stream_reader, args=(p.stdout, prefix), daemon=True).start()
        Thread(target=stream_reader, args=(p.stderr,f"{prefix} ERR"), daemon=True).start()
        
        return p
    except Exception as e:
        print(f"Failed to start {prefix}: {e}")
        return None

def main():
    print("🚀 Starting AIPipeline System...")
    
    # 1. Start Master
    print("Starting Master Server...")
    master = start_process(MASTER_CMD, prefix="MASTER")
    if master: processes.append(master)
    time.sleep(2) # Give master a moment to bind port

    # 2. Start Worker
    print("Starting Worker...")
    worker = start_process(WORKER_CMD, prefix="WORKER")
    if worker: processes.append(worker)

    # 3. Start Frontend
    print("Starting Frontend...")
    frontend = start_process(FRONTEND_CMD, cwd=FRONTEND_DIR, prefix="FRONTEND")
    if frontend: processes.append(frontend)

    print("\n✅ System running! Press Ctrl+C to stop.\n")
    print("   - Master: http://127.0.0.1:8002")
    print("   - Frontend: http://localhost:5173")
    print("-" * 50)

    try:
        while True:
            time.sleep(1)
            # Check if processes are alive
            if master.poll() is not None:
                print("❌ Master Server died!")
                break
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    finally:
        kill_all()

def kill_children(proc_pid):
    try:
        parent = psutil.Process(proc_pid)
        for child in parent.children(recursive=True):
            child.kill()
        parent.kill()
    except psutil.NoSuchProcess:
        pass

def kill_all():
    global processes
    for p in processes:
        if p.poll() is None:
            print(f"Killing PID {p.pid}...")
            # Use psutil to kill entire process tree (important for npm/shell)
            kill_children(p.pid)
            
if __name__ == "__main__":
    main()
