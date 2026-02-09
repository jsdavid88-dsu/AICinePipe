from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from loguru import logger
from ..websocket.connection_manager import manager
from ..services.worker_manager import WorkerManager
from ..services.job_manager import JobManager
from ..models.job import JobStatus
from ..dependencies import get_worker_manager, get_job_manager
import json

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    worker_manager: WorkerManager = Depends(get_worker_manager),
    job_manager: JobManager = Depends(get_job_manager),
):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                msg_type = msg.get("type")

                if msg_type == "heartbeat":
                    client_ip = websocket.client.host if websocket.client else "127.0.0.1"
                    worker_node = worker_manager.parse_heartbeat_message(client_id, msg, client_ip)
                    worker_manager.register_worker(worker_node)

                elif msg_type == "job_started":
                    job_id = msg.get("job_id")
                    logger.info(f"Job {job_id} started on worker {client_id}")
                    job_manager.update_job_status(job_id, JobStatus.RUNNING)

                elif msg_type == "job_completed":
                    job_id = msg.get("job_id")
                    output_files = msg.get("output_files", [])
                    logger.info(f"Job {job_id} completed with {len(output_files)} output(s)")
                    file_urls = [f.get("url", f.get("filename", "")) for f in output_files]
                    job_manager.set_job_output_files(job_id, file_urls)
                    job_manager.update_job_status(job_id, JobStatus.COMPLETED)

                elif msg_type == "job_failed":
                    job_id = msg.get("job_id")
                    error = msg.get("error", "Unknown error")
                    logger.error(f"Job {job_id} failed: {error}")
                    job_manager.update_job_status(job_id, JobStatus.FAILED, error)

                elif msg_type == "job_progress":
                    job_id = msg.get("job_id")
                    progress = msg.get("progress", 0.0)
                    job_manager.update_job_progress(job_id, progress)

                else:
                    logger.debug(f"Received from {client_id}: {data}")

            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket Error on {client_id}: {e}")
        manager.disconnect(client_id)

