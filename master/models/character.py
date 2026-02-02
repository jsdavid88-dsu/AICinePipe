from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum

class ClothingOption(BaseModel):
    id: str
    name: str
    description: str
    image_path: Optional[str] = None

class Character(BaseModel):
    id: str
    name: str
    description: str = Field(..., description="캐릭터의 기본 외형 설명")
    reference_sheet: str = Field(..., description="참조 이미지 경로")
    
    # LoRA 설정
    lora_path: Optional[str] = Field(None, description="캐릭터 전용 LoRA 파일 경로 (.safetensors)")
    lora_strength: float = Field(0.8, description="LoRA 적용 강도 (0.0 ~ 1.0)")
    trigger_words: List[str] = Field(default_factory=list, description="LoRA 트리거 단어들")
    use_lora: bool = Field(True, description="LoRA 사용 여부 토글")
    
    clothing_options: List[ClothingOption] = Field(default_factory=list)
    default_clothing: Optional[str] = None
    style_keywords: List[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "CHR-001",
                "name": "Luna",
                "description": "A cyberpunk female warrior with neon hair",
                "reference_sheet": "/projects/p1/assets/luna_ref.png",
                "lora_path": "luna_v1.safetensors",
                "lora_strength": 0.85,
                "trigger_words": ["luna_cyber", "neon_hair"],
                "use_lora": True
            }
        }
