from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Dict
import os
from ..dependencies import get_data_manager
from ..services.data_manager import DataManager

router = APIRouter(
    prefix="/projects",
    tags=["projects"]
)

@router.post("/", status_code=201)
async def create_project(
    project_id: str = Body(..., embed=True), 
    manager: DataManager = Depends(get_data_manager)
):
    success = manager.create_project(project_id)
    if not success:
        raise HTTPException(status_code=409, detail=f"Project {project_id} already exists")
    
    # 생성 후 바로 로드
    manager.load_project(project_id)
    return {"message": "Project created and loaded", "project_id": project_id}

@router.post("/{project_id}/load")
async def load_project(project_id: str, manager: DataManager = Depends(get_data_manager)):
    try:
        manager.load_project(project_id)
        return {"message": "Project loaded", "project_id": project_id}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Project not found")

@router.get("/")
async def list_projects(manager: DataManager = Depends(get_data_manager)):
    # projects 폴더 스캔
    if not os.path.exists(manager.projects_root):
        return []
        
    projects = [d for d in os.listdir(manager.projects_root) 
               if os.path.isdir(os.path.join(manager.projects_root, d))]
    return projects
