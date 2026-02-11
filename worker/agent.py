import asyncio
import websockets
import json
import argparse
import uuid
import platform
import os
import logging
from gpu_reporter import get_system_info
from comfy_client import ComfyClient
from job_executor import JobExecutor

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("worker.agent")

# 환경변수 기반 설정
COMFYUI_URL = os.getenv("COMFYUI_URL", "http://127.0.0.1:8188")
DEFAULT_MASTER_URL = os.getenv("MASTER_WS_URL", "ws://localhost:8002")

# Polling configuration
POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", "2.0"))
POLL_TIMEOUT = float(os.getenv("POLL_TIMEOUT", "600.0"))

# ID 생성 (또는 파일에서 로드)
NODE_ID = f"worker-{platform.node()}-{str(uuid.uuid4())[:8]}"

# Track current worker status for heartbeat reporting
_current_status = "idle"
_current_job_id = None


def _set_worker_status(status: str, job_id: str = None):
    global _current_status, _current_job_id
    _current_status = status
    _current_job_id = job_id


async def poll_comfyui_completion(comfy_client: ComfyClient, prompt_id: str,
                                  job_id: str, websocket):
    """Poll ComfyUI history API until the job completes or fails.

    Sends job_progress, job_completed, or job_failed messages back to master
    via the existing WebSocket connection.
    """
    logger.info(f"Starting completion polling for job={job_id} prompt={prompt_id}")
    _set_worker_status("busy", job_id)
    elapsed = 0.0

    try:
        while elapsed < POLL_TIMEOUT:
            await asyncio.sleep(POLL_INTERVAL)
            elapsed += POLL_INTERVAL

            try:
                history = comfy_client.get_history(prompt_id)
            except Exception as e:
                logger.warning(f"History poll failed (will retry): {e}")
                continue

            entry = history.get(prompt_id)
            if entry is None:
                # Job still queued or executing — not yet in history
                continue

            # Check for execution error in status
            status_info = entry.get("status", {})
            if status_info.get("status_str") == "error":
                messages = status_info.get("messages", [])
                error_detail = str(messages) if messages else "ComfyUI execution error"
                logger.error(f"Job {job_id} failed: {error_detail}")
                await websocket.send(json.dumps({
                    "type": "job_failed",
                    "job_id": job_id,
                    "prompt_id": prompt_id,
                    "node_id": NODE_ID,
                    "error": error_detail
                }))
                _set_worker_status("idle")
                return

            # Extract output files from completed history
            outputs = entry.get("outputs", {})
            output_files = []
            for node_id, node_output in outputs.items():
                for img in node_output.get("images", []):
                    filename = img.get("filename", "")
                    subfolder = img.get("subfolder", "")
                    img_type = img.get("type", "output")
                    url = comfy_client.get_images(filename, subfolder, img_type)
                    output_files.append({
                        "filename": filename,
                        "subfolder": subfolder,
                        "type": img_type,
                        "url": url
                    })
                for vid in node_output.get("gifs", []):
                    filename = vid.get("filename", "")
                    subfolder = vid.get("subfolder", "")
                    vid_type = vid.get("type", "output")
                    url = comfy_client.get_images(filename, subfolder, vid_type)
                    output_files.append({
                        "filename": filename,
                        "subfolder": subfolder,
                        "type": vid_type,
                        "url": url
                    })

            if status_info.get("completed", False) or outputs:
                logger.info(f"Job {job_id} completed with {len(output_files)} output(s)")
                await websocket.send(json.dumps({
                    "type": "job_completed",
                    "job_id": job_id,
                    "prompt_id": prompt_id,
                    "node_id": NODE_ID,
                    "output_files": output_files
                }))
                _set_worker_status("idle")
                return

        # Timeout reached
        logger.error(f"Job {job_id} timed out after {POLL_TIMEOUT}s")
        await websocket.send(json.dumps({
            "type": "job_failed",
            "job_id": job_id,
            "prompt_id": prompt_id,
            "node_id": NODE_ID,
            "error": f"Polling timed out after {POLL_TIMEOUT}s"
        }))
        _set_worker_status("idle")

    except websockets.exceptions.ConnectionClosed:
        logger.warning(f"Connection lost while polling job {job_id}")
        _set_worker_status("idle")
    except Exception as e:
        logger.error(f"Polling error for job {job_id}: {e}", exc_info=True)
        try:
            await websocket.send(json.dumps({
                "type": "job_failed",
                "job_id": job_id,
                "prompt_id": prompt_id,
                "node_id": NODE_ID,
                "error": f"Worker polling error: {str(e)}"
            }))
        except Exception:
            pass
        _set_worker_status("idle")


async def connect_to_master(master_url):
    uri = f"{master_url}/ws/{NODE_ID}"
    logger.info(f"Connecting to Master: {uri}")

    while True:
        try:
            async with websockets.connect(uri) as websocket:
                logger.info("Connected to Master!")

                # Initialize components
                # Use absolute path for workflows relative to this script
                current_dir = os.path.dirname(os.path.abspath(__file__))
                workflow_dir = os.path.abspath(os.path.join(current_dir, "../workflows"))
                
                comfy_client = ComfyClient(base_url=COMFYUI_URL)
                executor = JobExecutor(comfy_client, workflow_dir=workflow_dir)

                # Heartbeat Loop
                heartbeat_task = asyncio.create_task(send_heartbeat(websocket))

                # Track background polling tasks so they can be cleaned up
                polling_tasks = set()

                # Message Listen Loop
                while True:
                    message = await websocket.recv()
                    logger.debug(f"Received: {message}")
                    data = json.loads(message)

                    if data.get("type") == "job_assign":
                        job_data = data.get("job", {})
                        job_id = job_data.get("id")
                        logger.info(f"Job Assigned: {job_id}")
                        try:
                            # Execute Job (queue prompt to ComfyUI)
                            prompt_id = executor.execute_job(job_data, NODE_ID)

                            await websocket.send(json.dumps({
                                "type": "job_started",
                                "job_id": job_id,
                                "prompt_id": prompt_id,
                                "node_id": NODE_ID
                            }))

                            # Start background polling for completion
                            task = asyncio.create_task(
                                poll_comfyui_completion(
                                    comfy_client, prompt_id, job_id, websocket
                                )
                            )
                            polling_tasks.add(task)
                            task.add_done_callback(polling_tasks.discard)

                        except Exception as e:
                            logger.error(f"Job execution failed: {e}", exc_info=True)
                            await websocket.send(json.dumps({
                                "type": "job_failed",
                                "job_id": job_id,
                                "error": str(e),
                                "node_id": NODE_ID
                            }))

                    # Clean up completed polling tasks
                    polling_tasks = {t for t in polling_tasks if not t.done()}

        except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
            logger.warning(f"Connection lost: {e}. Reconnecting in 5s...")
            _set_worker_status("idle")
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            _set_worker_status("idle")
            await asyncio.sleep(5)

async def send_heartbeat(websocket):
    try:
        while True:
            info = get_system_info()
            await websocket.send(json.dumps({
                "type": "heartbeat",
                "node_id": NODE_ID,
                "status": _current_status,
                "job_id": _current_job_id,
                "info": info
            }))
            await asyncio.sleep(5)  # 5초마다 상태 보고
    except websockets.exceptions.ConnectionClosed:
        logger.warning("Heartbeat stopped: connection closed")
    except Exception as e:
        logger.error(f"Heartbeat error: {e}", exc_info=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--master", default=DEFAULT_MASTER_URL)
    args = parser.parse_args()

    try:
        asyncio.run(connect_to_master(args.master))
    except KeyboardInterrupt:
        logger.info("Worker stopped.")
