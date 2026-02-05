from fastapi import APIRouter, HTTPException, Depends
from typing import List
from ..models.worker import WorkerNode, WorkerStatus
from ..services.worker_manager import WorkerManager
from ..dependencies import get_worker_manager

router = APIRouter(
    prefix="/workers",
    tags=["workers"]
)

@router.post("/register", response_model=WorkerNode)
async def register_worker(worker: WorkerNode, manager: WorkerManager = Depends(get_worker_manager)):
    """Register a new worker or update existing one."""
    return manager.register_worker(worker)

@router.post("/{worker_id}/heartbeat")
async def heartbeat(worker_id: str, manager: WorkerManager = Depends(get_worker_manager)):
    """Update worker heartbeat."""
    success = manager.update_heartbeat(worker_id)
    if not success:
        raise HTTPException(status_code=404, detail="Worker not found")
    return {"status": "ok"}

@router.get("/", response_model=List[WorkerNode])
async def list_workers(manager: WorkerManager = Depends(get_worker_manager)):
    """List all active workers."""
    # 30 second timeout for active status
    return manager.get_active_workers(timeout_seconds=30)

@router.delete("/{worker_id}")
async def unregister_worker(worker_id: str, manager: WorkerManager = Depends(get_worker_manager)):
    """Manually remove a worker."""
    manager.remove_worker(worker_id)
    return {"status": "removed"}
