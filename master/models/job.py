from typing import Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class JobStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobPriority(int, Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3

class Job(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    shot_id: Optional[str] = None
    
    workflow_type: str  # Shot의 WorkflowType과 매핑
    params: Dict[str, Any] = Field(default_factory=dict, description="워크플로우 실행 파라미터")
    
    # 리소스 요구사항
    vram_required_gb: int = Field(8, description="최소 요구 VRAM")
    gpu_count_required: int = Field(1, description="필요 GPU 수")
    
    # 상태
    status: JobStatus = JobStatus.PENDING
    priority: JobPriority = JobPriority.NORMAL
    progress: float = 0.0
    
    # 실행 정보
    assigned_worker_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    output_files: list[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True
