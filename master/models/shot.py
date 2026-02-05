from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field

class ShotStatus(str, Enum):
    PENDING = "pending"              # 대기 중
    QUEUED = "queued"                # 큐에 등록됨
    GENERATING = "generating"        # 생성 중
    COMPLETED = "completed"          # 생성 완료
    FAILED = "failed"                # 생성 실패
    NEEDS_REVISION = "needs_revision" # 수정 필요
    APPROVED = "approved"            # 컨펌 완료

class WorkflowType(str, Enum):
    # Image Generation
    TEXT_TO_IMAGE = "text_to_image"
    
    # Video Generation
    WAN_ANIMATE = "wan_animate"
    LTX2 = "ltx2"
    SVI = "svi"
    TELESTYLE = "telestyle"
    I2V_KLING = "i2v_kling"
    FFLF = "fflf"
    FRAME_SPLIT = "frame_split"

class ShotSubject(BaseModel):
    character_id: str
    action: str = ""
    costume_override: Optional[str] = None
    lora_weight: float = 1.0

class TechnicalSpecs(BaseModel):
    camera: Optional[str] = "Arri Alexa"
    film_stock: Optional[str] = "Kodak Vision3"
    lighting: Optional[str] = None
    lens: Optional[str] = "Anamorphic"
    aspect_ratio: str = "16:9"
    filter: List[str] = []

class Environment(BaseModel):
    location: str = ""
    weather: Optional[str] = None
    time_of_day: Optional[str] = None
    reference_image: Optional[str] = None # Path to image
    
class Shot(BaseModel):
    id: str = Field(..., description="SHT-00001 형식의 고유 ID")
    sequence_id: Optional[str] = None 
    
    # Core Content
    scene_description: str
    dialogue: Optional[str] = None
    
    # Structured Data (V2)
    subjects: List[ShotSubject] = Field(default_factory=list)
    environment: Environment = Field(default_factory=Environment)
    technical: TechnicalSpecs = Field(default_factory=TechnicalSpecs)
    
    # Legacy Fields (Deprecated but kept for manual overrides or fallback)
    action: Optional[str] = None 
    character_ids: List[str] = Field(default_factory=list) # Sync with subjects?
    cinematic_id: Optional[str] = None # Link to CinematicOption preset
    
    # 생성 정보
    generated_prompt: Optional[str] = None
    negative_prompt: Optional[str] = None
    seed: Optional[int] = None
    
    # 미디어 경로
    reference_images: List[str] = Field(default_factory=list)
    generated_image_path: Optional[str] = None
    generated_video_path: Optional[str] = None
    
    # 타임라인 정보
    frame_count: int = Field(24, description="프레임 수")
    fps: float = Field(24.0, description="초당 프레임")
    duration_seconds: float = Field(1.0, description="재생 시간 (초)")
    timecode_in: Optional[str] = None
    timecode_out: Optional[str] = None
    
    # 상태 및 워크플로우
    status: ShotStatus = ShotStatus.PENDING
    workflow_type: WorkflowType = WorkflowType.TEXT_TO_IMAGE
    
    # 메타데이터
    created_at: str
    updated_at: str

    class Config:
        use_enum_values = True
