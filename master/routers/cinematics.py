from fastapi import APIRouter, HTTPException
from typing import List, Dict
from ..services.preset_service import preset_service

router = APIRouter(
    prefix="/cinematics",
    tags=["cinematics"]
)

@router.get("/presets", response_model=List[Dict])
async def get_cinematic_presets():
    """Returns list of available cinematic presets with mapped image URLs."""
    return preset_service.get_all()

@router.get("/presets/{preset_id}")
async def get_preset_detail(preset_id: str):
    preset = preset_service.get_by_id(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    return preset

@router.post("/scan")
async def scan_presets():
    """Reloads presets from disk."""
    preset_service.load_presets()
    return {"status": "ok", "count": len(preset_service.get_all())}
