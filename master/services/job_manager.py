"""
Job manager with SQLite persistence.

Jobs survive server restarts. Based on DirectorsConsole JobRepository pattern.
"""

import json
from typing import List, Optional
from datetime import datetime

from loguru import logger

from ..db.database import get_database
from ..models.job import Job, JobStatus
from ..services.data_manager import DataManager


class JobManager:
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.db = get_database()

    def create_job(self, project_id: str, shot_id: str, workflow_type: str, params: dict) -> Job:
        job = Job(
            project_id=project_id,
            shot_id=shot_id,
            workflow_type=workflow_type,
            params=params,
        )
        self._save_job(job)
        logger.info(f"Job created: {job.id} (project={project_id}, type={workflow_type})")
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        row = self.db.fetchone("SELECT * FROM jobs WHERE id = ?", (job_id,))
        return self._row_to_job(row) if row else None

    def list_jobs(self, project_id: Optional[str] = None) -> List[Job]:
        if project_id:
            rows = self.db.fetchall(
                "SELECT * FROM jobs WHERE project_id = ? ORDER BY created_at DESC",
                (project_id,),
            )
        else:
            rows = self.db.fetchall("SELECT * FROM jobs ORDER BY created_at DESC")
        return [self._row_to_job(r) for r in rows]

    def update_job_status(self, job_id: str, status: JobStatus, message: Optional[str] = None):
        job = self.get_job(job_id)
        if not job:
            logger.warning(f"Job {job_id} not found for status update")
            return

        job.status = status
        if message:
            job.error_message = message

        if status == JobStatus.RUNNING:
            job.started_at = datetime.now()
        elif status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            job.completed_at = datetime.now()

        self._save_job(job)
        logger.info(f"Job {job_id} status -> {status}")

    def get_pending_job(self) -> Optional[Job]:
        """Get next pending job (FIFO by creation time)."""
        row = self.db.fetchone(
            "SELECT * FROM jobs WHERE status = ? ORDER BY created_at ASC LIMIT 1",
            (JobStatus.PENDING.value,),
        )
        return self._row_to_job(row) if row else None

    def assign_job(self, job_id: str, worker_id: str):
        job = self.get_job(job_id)
        if job and job.status == JobStatus.PENDING:
            job.status = JobStatus.ASSIGNED
            job.assigned_worker_id = worker_id
            self._save_job(job)
            logger.info(f"Job {job_id} assigned to worker {worker_id}")

    def update_job_progress(self, job_id: str, progress: float):
        """Update job progress without full reload."""
        self.db.execute(
            "UPDATE jobs SET progress = ? WHERE id = ?",
            (progress, job_id),
        )

    def set_job_output_files(self, job_id: str, output_files: list[str]):
        """Update output files for a completed job."""
        self.db.execute(
            "UPDATE jobs SET output_files = ? WHERE id = ?",
            (json.dumps(output_files), job_id),
        )

    # -- Persistence helpers --

    def _save_job(self, job: Job) -> None:
        """Insert or replace a job row."""
        self.db.execute(
            """INSERT OR REPLACE INTO jobs (
                id, project_id, shot_id, workflow_type, params,
                vram_required_gb, gpu_count_required,
                status, priority, progress,
                assigned_worker_id, created_at, started_at, completed_at,
                error_message, output_files
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                job.id,
                job.project_id,
                job.shot_id,
                job.workflow_type,
                json.dumps(job.params, ensure_ascii=False),
                job.vram_required_gb,
                job.gpu_count_required,
                job.status if isinstance(job.status, str) else job.status.value,
                job.priority if isinstance(job.priority, int) else job.priority.value,
                job.progress,
                job.assigned_worker_id,
                job.created_at.isoformat() if isinstance(job.created_at, datetime) else job.created_at,
                job.started_at.isoformat() if isinstance(job.started_at, datetime) else job.started_at,
                job.completed_at.isoformat() if isinstance(job.completed_at, datetime) else job.completed_at,
                job.error_message,
                json.dumps(job.output_files, ensure_ascii=False),
            ),
        )

    @staticmethod
    def _row_to_job(row: dict) -> Job:
        """Convert a SQLite row dict to a Job model."""
        data = dict(row)

        # Parse JSON fields
        params = data.get("params", "{}")
        if isinstance(params, str):
            try:
                data["params"] = json.loads(params)
            except (json.JSONDecodeError, TypeError):
                data["params"] = {}

        output = data.get("output_files", "[]")
        if isinstance(output, str):
            try:
                data["output_files"] = json.loads(output)
            except (json.JSONDecodeError, TypeError):
                data["output_files"] = []

        # Parse datetimes
        for field in ("created_at", "started_at", "completed_at"):
            val = data.get(field)
            if isinstance(val, str) and val:
                try:
                    data[field] = datetime.fromisoformat(val)
                except ValueError:
                    data[field] = None
            elif not val:
                if field == "created_at":
                    data[field] = datetime.now()
                else:
                    data[field] = None

        return Job(**data)
