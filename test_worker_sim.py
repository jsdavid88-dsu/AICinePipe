import asyncio
import websockets
import json
import uuid

MASTER_URL = "ws://localhost:8002/ws"

async def simulate_worker():
    worker_id = f"worker-{uuid.uuid4().hex[:8]}"
    print(f"Connecting as {worker_id}...")
    
    async with websockets.connect(f"{MASTER_URL}/{worker_id}") as websocket:
        # 1. Send Registration / Handshake
        # The backend expects a heartbeat or just connection?
        # Master websocket endpoint: await manager.connect(websocket, worker_id)
        # Then it waits for messages.
        # Worker usually sends a heartbeat with specs.
        
        specs = {
            "type": "heartbeat",
            "client_id": worker_id,
            "status": "online",
            "vram_total": 24.0, # simulates a 3090/4090
            "vram_free": 24.0,
            "gpus": [{"name": "NVIDIA GeForce RTX 4090", "memory_total_mb": 24576, "memory_used_mb": 0}]
        }
        
        await websocket.send(json.dumps(specs))
        print("Sent heartbeat/registration.")
        
        # 2. Listen for Job Assignment
        print("Waiting for job...")
        try:
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                print(f"Received: {data}")
                
                if data.get("type") == "job_assign":
                    print(f"Job assigned! ID: {data['job_id']}")
                    # Simulate acceptance
                    await websocket.send(json.dumps({
                        "type": "job_status",
                        "job_id": data['job_id'],
                        "status": "running"
                    }))
                    print("Accepted job.")
                    break
        except websockets.ConnectionClosed:
            print("Connection closed.")

if __name__ == "__main__":
    asyncio.run(simulate_worker())
