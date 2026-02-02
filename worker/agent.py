import asyncio
import websockets
import json
import argparse
import uuid
import platform
from gpu_reporter import get_system_info
from comfy_client import ComfyClient
from job_executor import JobExecutor

# ID 생성 (또는 파일에서 로드)
NODE_ID = f"worker-{platform.node()}-{str(uuid.uuid4())[:8]}"

async def connect_to_master(master_url):
    uri = f"{master_url}/ws/{NODE_ID}"
    print(f"Connecting to Master: {uri}")
    
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                print("Connected to Master!")
                
                # Initialize components
                comfy_client = ComfyClient(base_url="http://127.0.0.1:8188")
                executor = JobExecutor(comfy_client, workflow_dir="../workflows")

                # Heartbeat Loop
                heartbeat_task = asyncio.create_task(send_heartbeat(websocket))
                
                # Message Listen Loop
                while True:
                    message = await websocket.recv()
                    print(f"Received: {message}")
                    data = json.loads(message)
                    
                    if data.get("type") == "job_assign":
                        print("Job Assigned! Processing...")
                        try:
                            # Execute Job
                            prompt_id = executor.execute_job(data.get("job"), NODE_ID)
                            
                            await websocket.send(json.dumps({
                                "type": "job_started",
                                "job_id": data.get("job").get("id"),
                                "prompt_id": prompt_id,
                                "node_id": NODE_ID
                            }))
                            
                            # Note: Completion status normally comes from polling history or websocket from ComfyUI
                            # For now, we assume queued = running. 
                            # A real implementation would loop checking status via executor.
                            
                        except Exception as e:
                            print(f"Job execution failed: {e}")
                            await websocket.send(json.dumps({
                                "type": "job_failed",
                                "job_id": data.get("job").get("id"),
                                "error": str(e)
                            }))
                        
        except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError):
            print("Connection lost. Reconnecting in 5s...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(5)

async def send_heartbeat(websocket):
    try:
        while True:
            info = get_system_info()
            await websocket.send(json.dumps({
                "type": "heartbeat",
                "node_id": NODE_ID,
                "status": "idle",
                "info": info
            }))
            await asyncio.sleep(5) # 5초마다 상태 보고
    except Exception:
        pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--master", default="ws://localhost:8002")
    args = parser.parse_args()
    
    try:
        asyncio.run(connect_to_master(args.master))
    except KeyboardInterrupt:
        print("Worker stopped.")
