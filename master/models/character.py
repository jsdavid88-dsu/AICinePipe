from typing import List, Optional
from pydantic import BaseModel, Field

class Character(BaseModel):
    id: str
    name: str
    description: Optional[str] = ""
    reference_sheet: Optional[str] = None
    
    # LoRA 설정
    lora_path: Optional[str] = None
    lora_strength: float = 0.8
    trigger_words: Optional[str] = ""  # Comma separated string for simplicity in DataTable
    use_lora: bool = False  # LoRA 사용 여부
    
    # Appearance
    default_clothing: Optional[str] = None  # 기본 의상 설정
    
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
