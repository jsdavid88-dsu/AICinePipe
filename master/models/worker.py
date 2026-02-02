from typing import List, Dict, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime

class WorkerStatus(str, Enum):
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"

class GPUInfo(BaseModel):
    index: int
    name: str
    memory_total: int  # MB
    memory_used: int   # MB
    utilization: int   # %
    temperature: int   # Celsius

class WorkerNode(BaseModel):
    id: str  # 고유 ID (MAC 주소 또는 UUID)
    hostname: str
    ip_address: str
    port: int
    
    status: WorkerStatus = WorkerStatus.OFFLINE
    gpus: List[GPUInfo] = Field(default_factory=list)
    system_info: Dict[str, Any] = Field(default_factory=dict) # CPU, RAM 등
    
    current_job_id: Optional[str] = None
    supported_workflows: List[str] = Field(default_factory=list)
    
    last_heartbeat: datetime = Field(default_factory=datetime.now)
    joined_at: datetime = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True
