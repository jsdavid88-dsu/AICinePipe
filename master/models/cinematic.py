from typing import List, Optional
from pydantic import BaseModel, Field

class CinematicOption(BaseModel):
    id: str
    name: str
    category: Optional[str] = "General"

    # Camera & Lens
    camera_body: Optional[str] = "Arri Alexa"
    focal_length: Optional[str] = "35mm"
    lens_type: Optional[str] = "Anamorphic"
    film_stock: Optional[str] = None

    # Scene & Lighting
    shot_type: Optional[str] = None
    lighting: Optional[str] = None
    
    # Mood & Style
    style: Optional[str] = "Cinematic"
    environment: Optional[str] = ""
    atmosphere: Optional[str] = ""
    
    filters: Optional[List[str]] = []
    
    # Backup
    raw_data: Optional[dict] = None

    created_at: Optional[str] = None
    updated_at: Optional[str] = None
