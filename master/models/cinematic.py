from typing import List, Optional
from pydantic import BaseModel, Field

class CinematicOption(BaseModel):
    id: str
    name: str = Field(..., description="옵션 세트 이름")
    
    # 카메라 및 렌즈
    camera_body: Optional[str] = Field(None, description="e.g. Arri Alexa, Sony FX6")
    focal_length: Optional[str] = Field(None, description="e.g. 35mm, 50mm, 85mm")
    lens_type: Optional[str] = Field(None, description="e.g. Anamorphic, Vintage, Macro")
    
    # 시각 스타일
    film_stock: Optional[str] = Field(None, description="e.g. Kodak Vision3 500T")
    style: Optional[str] = Field(None, description="e.g. Photorealistic, Anime, Oil Painting")
    look_and_feel: Optional[str] = Field(None, description="e.g. Dune style, Blade Runner style")
    
    # 조명 및 환경
    lighting_source: Optional[str] = Field(None, description="e.g. Natural, Neon, Studio Softbox")
    lighting_style: Optional[str] = Field(None, description="e.g. Rembrandt, High Key, Chiaroscuro")
    environment: Optional[str] = Field(None, description="배경/환경 설명")
    atmosphere: Optional[str] = Field(None, description="분위기, e.g. Hazy, Rainy, Sunny")
    
    # 기타
    filter_type: Optional[str] = Field(None, description="렌즈 필터 효과")
    aspect_ratio: str = Field("16:9", description="화면 비율")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "CINE-001",
                "name": "Sci-Fi Movie Look",
                "camera_body": "Arri Alexa LF",
                "focal_length": "35mm",
                "lens_type": "Anamorphic",
                "film_stock": "Kodak Vision3 500T",
                "style": "Photorealistic",
                "lighting_source": "Neon and Practical",
                "aspect_ratio": "2.39:1"
            }
        }
