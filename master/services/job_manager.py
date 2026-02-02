from typing import List, Optional, Dict
from datetime import datetime
import asyncio
from ..models.job import Job, JobStatus
from ..services.data_manager import DataManager

class JobManager:
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.jobs: Dict[str, Job] = {} # In-memory job queue (Production would use Redis/DB)
        self.queue: List[str] = []     # Pending job IDs

    def create_job(self, project_id: str, shot_id: str, workflow_type: str, params: dict) -> Job:
        job = Job(
            project_id=project_id,
            shot_id=shot_id,
            workflow_type=workflow_type,
            params=params
        )
        self.jobs[job.id] = job
        self.queue.append(job.id)
        # TODO: Persist jobs to DB
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        return self.jobs.get(job_id)

    def list_jobs(self, project_id: Optional[str] = None) -> List[Job]:
        if project_id:
            return [j for j in self.jobs.values() if j.project_id == project_id]
        return list(self.jobs.values())

    def update_job_status(self, job_id: str, status: JobStatus, message: Optional[str] = None):
        job = self.jobs.get(job_id)
        if not job:
            return
        
        job.status = status
        if message:
            job.error_message = message
            
        if status == JobStatus.RUNNING:
            job.started_at = datetime.now()
        elif status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            job.completed_at = datetime.now()

    def get_pending_job(self) -> Optional[Job]:
        # Simple FIFO queue
        # TODO: Priority queue & Resource matching
        for job_id in self.queue:
            job = self.jobs[job_id]
            if job.status == JobStatus.PENDING:
                return job
        return None
        
    def assign_job(self, job_id: str, worker_id: str):
        job = self.jobs.get(job_id)
        if job and job.status == JobStatus.PENDING:
            job.status = JobStatus.ASSIGNED
            job.assigned_worker_id = worker_id
            # Remove from pending queue logic would go here
