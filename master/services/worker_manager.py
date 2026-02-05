from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from ..models.worker import WorkerNode, WorkerStatus, GPUInfo


class WorkerManager:
    def __init__(self):
        # In-memory storage for active workers
        # {worker_id: WorkerNode}
        self.workers: Dict[str, WorkerNode] = {}
        
    def register_worker(self, worker_info: WorkerNode) -> WorkerNode:
        """Register or update a worker node."""
        worker_info.last_heartbeat = datetime.now()
        worker_info.status = WorkerStatus.IDLE if worker_info.status == WorkerStatus.OFFLINE else worker_info.status
        self.workers[worker_info.id] = worker_info
        return worker_info

    def parse_heartbeat_message(self, client_id: str, msg: Dict[str, Any], client_ip: str = "127.0.0.1") -> WorkerNode:
        """
        Parse a WebSocket heartbeat message and convert it to a WorkerNode.
        This centralizes the mapping logic for cleaner router code.
        """
        info = msg.get("info", {})
        gpus_data = info.get("gpus", [])
        
        mapped_gpus = []
        for g in gpus_data:
            mapped_gpus.append(GPUInfo(
                index=g.get("id", 0),
                name=g.get("name", "Unknown"),
                memory_total=g.get("memory_total", 0),
                memory_used=g.get("memory_used", 0),
                utilization=int(g.get("load", 0)),
                temperature=g.get("temperature", 0)
            ))
        
        worker_node = WorkerNode(
            id=client_id,
            hostname=info.get("hostname", client_id),
            ip_address=client_ip,
            port=0,  # Unknown via WebSocket
            status=msg.get("status", "idle"),
            gpus=mapped_gpus,
            system_info={
                "cpu_usage": info.get("cpu_usage", 0),
                "ram_usage": info.get("ram_usage", 0),
                "os": info.get("os", "Unknown")
            },
            last_heartbeat=datetime.now()
        )
        
        return worker_node

    def update_heartbeat(self, worker_id: str) -> bool:
        """Update the last heartbeat timestamp for a worker."""
        if worker_id in self.workers:
            self.workers[worker_id].last_heartbeat = datetime.now()
            # If it was offline, mark as idle (assuming it's back)
            if self.workers[worker_id].status == WorkerStatus.OFFLINE:
                 self.workers[worker_id].status = WorkerStatus.IDLE
            return True
        return False

    def update_status(self, worker_id: str, status: WorkerStatus, current_job_id: Optional[str] = None) -> bool:
        """Update worker status (e.g., BUSY, IDLE)."""
        if worker_id in self.workers:
            self.workers[worker_id].status = status
            self.workers[worker_id].current_job_id = current_job_id
            self.workers[worker_id].last_heartbeat = datetime.now()
            return True
        return False

    def get_active_workers(self, timeout_seconds: int = 30) -> List[WorkerNode]:
        """Return list of workers considered active (recent heartbeat)."""
        active = []
        now = datetime.now()
        threshold = timedelta(seconds=timeout_seconds)
        
        for w in self.workers.values():
            if now - w.last_heartbeat < threshold:
                active.append(w)
            else:
                # Mark as offline if timed out
                if w.status != WorkerStatus.OFFLINE:
                    w.status = WorkerStatus.OFFLINE
                # We typically still return 'offline' workers so admin can see them
                active.append(w) 
                
        return active

    def get_worker(self, worker_id: str) -> Optional[WorkerNode]:
        return self.workers.get(worker_id)
        
    def remove_worker(self, worker_id: str):
        if worker_id in self.workers:
            del self.workers[worker_id]

