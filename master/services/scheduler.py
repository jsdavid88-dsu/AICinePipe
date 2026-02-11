"""
Scheduler — VRAM-aware job assignment to worker nodes.

Replaces the simple FIFO queue with intelligent backend selection
based on VRAM requirements, worker health, and load balancing.
"""

import asyncio
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

from ..utils import logger
from ..models.job import Job


# =============================================================================
# VRAM REQUIREMENTS TABLE
# =============================================================================

# Default VRAM requirements (GB) by workflow type / model
VRAM_REQUIREMENTS: dict[str, float] = {
    # Image Generation
    "flux_t2i": 14.0,
    "flux_i2i": 14.0,
    "sdxl_t2i": 8.0,
    "sdxl_i2i": 8.0,
    "sd15_t2i": 4.0,
    "sd15_i2i": 4.0,
    "controlnet": 16.0,
    "inpainting": 10.0,
    # Image Editing
    "qwen_image_edit": 10.0,
    "instruct_pix2pix": 8.0,
    # Video Generation (i2v)
    "wan_animate": 20.0,
    "wan_2_2": 20.0,
    "ltx_2": 36.0,
    "svi": 20.0,
    "cogvideox": 24.0,
    "hunyuan_video": 24.0,
    # Post-processing
    "rife_interpolation": 4.0,
    "real_esrgan": 4.0,
    "upscale": 6.0,
    # Default
    "default": 8.0,
}


@dataclass
class WorkerInfo:
    """Information about a connected worker."""
    worker_id: str
    name: str
    host: str
    port: int
    gpus: list[dict] = field(default_factory=list)
    status: str = "unknown"  # online, busy, offline, error
    current_job_id: Optional[str] = None
    last_heartbeat: Optional[datetime] = None
    is_simulated: bool = False  # True if GPU data is fake

    @property
    def total_vram_gb(self) -> float:
        """Total VRAM across all GPUs in GB."""
        total = 0.0
        for gpu in self.gpus:
            total += gpu.get("memory_total_mb", 0) / 1024.0
        return total

    @property
    def free_vram_gb(self) -> float:
        """Available VRAM across all GPUs in GB."""
        total = 0.0
        for gpu in self.gpus:
            total_mb = gpu.get("memory_total_mb", 0)
            used_mb = gpu.get("memory_used_mb", 0)
            total += (total_mb - used_mb) / 1024.0
        return total

    @property
    def is_available(self) -> bool:
        """Check if worker is available for new jobs."""
        return self.status == "online" and self.current_job_id is None


class Scheduler:
    """VRAM-aware job scheduler for worker nodes."""

    def __init__(self):
        self._workers: dict[str, WorkerInfo] = {}
        self._lock = asyncio.Lock()
        logger.info("Scheduler initialized with VRAM-aware assignment")

    async def register_worker(self, worker: WorkerInfo) -> None:
        """Register or update a worker."""
        async with self._lock:
            self._workers[worker.worker_id] = worker
        logger.info(
            f"Worker registered: {worker.name} ({worker.worker_id}) "
            f"— {worker.total_vram_gb:.1f}GB VRAM"
        )
        
        # Trigger check for pending jobs
        await self.check_for_pending_jobs()

    async def check_for_pending_jobs(self):
        """Check for pending jobs and assign to available workers."""
        from ..dependencies import get_job_manager
        job_manager = get_job_manager()
        
        for _ in range(5):
            job = job_manager.get_pending_job()
            if not job:
                break
                
            worker = await self.schedule_job(job)
            if not worker:
                # Re-queue the job so it isn't lost
                job_manager.requeue_job(job)
                break

    async def unregister_worker(self, worker_id: str) -> None:
        """Remove a worker from the pool."""
        async with self._lock:
            if worker_id in self._workers:
                name = self._workers[worker_id].name
                del self._workers[worker_id]
                logger.info(f"Worker unregistered: {name} ({worker_id})")

    async def schedule_job(self, job: Job) -> Optional[WorkerInfo]:
        """
        Attempt to schedule a job to a worker.
        """
        # 1. Determine VRAM requirements
        required_vram = self.get_vram_requirement(job.workflow_type)
        
        # 2. Select best worker
        worker = self.select_worker(job.workflow_type, required_vram)
        
        if not worker:
            return None
            
        # 3. Assign Job (WebSocket Communication)
        # We need access to the WebSocket manager here. 
        # Ideally, Scheduler should have a reference or be passed the manager.
        # But for cleaner dependency injection, let's import the global manager.
        
        from ..websocket.connection_manager import manager as ws_manager
        
        try:
            logger.info(f"Assigning job {job.id} to worker {worker.worker_id}")
            
            payload = {
                "type": "job_assign",
                "job": job.dict(),
                "job_id": job.id
            }
            
            await ws_manager.send_personal_message(payload, worker.worker_id)
            
            # 4. Update Worker Status locally
            worker.status = "busy"
            worker.current_job_id = job.id
            
            return worker
            
        except Exception as e:
            logger.error(f"Failed to dispatch job to worker {worker.worker_id}: {e}")
            return None

    def update_worker_status(
        self,
        worker_id: str,
        status: str,
        gpus: Optional[list[dict]] = None,
        current_job_id: Optional[str] = None,
    ) -> None:
        """Update worker status and GPU info."""
        worker = self._workers.get(worker_id)
        if not worker:
            return
        worker.status = status
        worker.last_heartbeat = datetime.now(timezone.utc)
        if gpus is not None:
            worker.gpus = gpus
        if current_job_id is not None:
            worker.current_job_id = current_job_id

    def select_worker(
        self,
        workflow_type: str = "default",
        required_vram_gb: Optional[float] = None,
    ) -> Optional[WorkerInfo]:
        """
        Select the best available worker for a job.

        Priority:
        1. Worker has enough VRAM
        2. Worker is not simulated (real GPU data preferred)
        3. Worker with most free VRAM (load balancing)
        """
        vram_needed = required_vram_gb or VRAM_REQUIREMENTS.get(
            workflow_type, VRAM_REQUIREMENTS["default"]
        )

        candidates = []
        for worker in list(self._workers.values()):
            if not worker.is_available:
                continue

            # Skip if not enough VRAM
            if worker.free_vram_gb < vram_needed:
                logger.debug(
                    f"Worker {worker.name} skipped: {worker.free_vram_gb:.1f}GB free "
                    f"< {vram_needed:.1f}GB required"
                )
                continue

            candidates.append(worker)

        if not candidates:
            logger.warning(
                f"No worker available for {workflow_type} "
                f"(needs {vram_needed:.1f}GB VRAM)"
            )
            return None

        # Sort: prefer real GPU data, then most free VRAM
        candidates.sort(
            key=lambda w: (not w.is_simulated, w.free_vram_gb),
            reverse=True,
        )

        selected = candidates[0]
        logger.info(
            f"Selected worker {selected.name} for {workflow_type} "
            f"({selected.free_vram_gb:.1f}GB free, needs {vram_needed:.1f}GB)"
        )
        return selected

    def get_all_workers(self) -> list[WorkerInfo]:
        """Get all registered workers."""
        return list(self._workers.values())

    def get_available_workers(self) -> list[WorkerInfo]:
        """Get all available (online, idle) workers."""
        return [w for w in self._workers.values() if w.is_available]

    def get_worker(self, worker_id: str) -> Optional[WorkerInfo]:
        """Get a specific worker by ID."""
        return self._workers.get(worker_id)

    def get_vram_requirement(self, workflow_type: str) -> float:
        """Get VRAM requirement for a workflow type."""
        return VRAM_REQUIREMENTS.get(workflow_type, VRAM_REQUIREMENTS["default"])

    def get_stats(self) -> dict:
        """Get scheduler statistics."""
        workers = list(self._workers.values())
        return {
            "total_workers": len(workers),
            "online_workers": sum(1 for w in workers if w.status == "online"),
            "busy_workers": sum(1 for w in workers if w.status == "busy"),
            "offline_workers": sum(1 for w in workers if w.status == "offline"),
            "total_vram_gb": sum(w.total_vram_gb for w in workers),
            "free_vram_gb": sum(w.free_vram_gb for w in workers if w.status == "online"),
            "simulated_workers": sum(1 for w in workers if w.is_simulated),
        }
