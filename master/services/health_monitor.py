"""
Health Monitor — periodic worker health checks and auto-recovery.

Polls worker endpoints at configurable intervals. Detects offline workers
and marks jobs for reassignment.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional, Callable

from ..utils import logger
from .scheduler import Scheduler, WorkerInfo


class HealthMonitor:
    """Monitors worker health and triggers recovery actions."""

    def __init__(
        self,
        scheduler: Scheduler,
        poll_interval: float = 10.0,
        offline_threshold: float = 30.0,
        on_worker_offline: Optional[Callable[[str], None]] = None,
    ):
        self._scheduler = scheduler
        self._poll_interval = poll_interval
        self._offline_threshold = timedelta(seconds=offline_threshold)
        self._on_worker_offline = on_worker_offline
        self._running = False
        self._task: Optional[asyncio.Task] = None
        logger.info(
            f"HealthMonitor initialized: poll={poll_interval}s, "
            f"offline threshold={offline_threshold}s"
        )

    async def start(self):
        """Start polling loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("HealthMonitor started")

    async def stop(self):
        """Stop polling loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("HealthMonitor stopped")

    async def _poll_loop(self):
        """Main polling loop."""
        while self._running:
            try:
                await self._check_all_workers()
            except Exception as e:
                logger.error(f"HealthMonitor poll error: {e}")
            await asyncio.sleep(self._poll_interval)

    async def _check_all_workers(self):
        """Check all registered workers."""
        now = datetime.now(timezone.utc)
        workers = self._scheduler.get_all_workers()

        for worker in workers:
            if worker.status == "offline":
                continue

            # Check heartbeat timeout
            if worker.last_heartbeat:
                time_since = now - worker.last_heartbeat
                if time_since > self._offline_threshold:
                    logger.warning(
                        f"Worker {worker.name} ({worker.worker_id}) has not "
                        f"sent heartbeat in {time_since.total_seconds():.0f}s — marking offline"
                    )
                    self._scheduler.update_worker_status(
                        worker.worker_id, "offline"
                    )

                    # Trigger recovery callback
                    if self._on_worker_offline and worker.current_job_id:
                        self._on_worker_offline(worker.worker_id)

    def get_status(self) -> dict:
        """Get health monitor status."""
        stats = self._scheduler.get_stats()
        return {
            "running": self._running,
            "poll_interval_seconds": self._poll_interval,
            "offline_threshold_seconds": self._offline_threshold.total_seconds(),
            **stats,
        }
