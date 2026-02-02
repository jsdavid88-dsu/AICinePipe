from fastapi import APIRouter, HTTPException, Depends
from typing import List
from ..models.shot import Shot
from ..dependencies import get_data_manager
from ..services.data_manager import DataManager

router = APIRouter(
    prefix="/shots",
    tags=["shots"]
)

@router.get("/", response_model=List[Shot])
async def get_shots(manager: DataManager = Depends(get_data_manager)):
    if not manager.current_project_id:
        raise HTTPException(status_code=400, detail="No project loaded")
    return manager.get_shots()

@router.post("/", response_model=Shot)
async def create_shot(shot: Shot, manager: DataManager = Depends(get_data_manager)):
    if not manager.current_project_id:
        raise HTTPException(status_code=400, detail="No project loaded")
    
    # 중복 ID 체크 등은 DataManager에서 처리하거나 여기서 처리
    manager.add_shot(shot)
    return shot

@router.put("/{shot_id}", response_model=Shot)
async def update_shot(shot_id: str, updates: dict, manager: DataManager = Depends(get_data_manager)):
    if not manager.current_project_id:
        raise HTTPException(status_code=400, detail="No project loaded")
    
    updated_shot = manager.update_shot(shot_id, updates)
    if not updated_shot:
        raise HTTPException(status_code=404, detail="Shot not found")
    return updated_shot
