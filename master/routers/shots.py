from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from ..models.shot import Shot
from ..dependencies import get_data_manager, get_workflow_analyzer
from ..services.data_manager import DataManager
from ..services.workflow_analyzer import WorkflowAnalyzer
from ..utils import id_generator, logger
from datetime import datetime
import os
import sys
import subprocess
import platform

router = APIRouter(
    prefix="/shots",
    tags=["shots"]
)


# Request models for new endpoints
class CreateShotRequest(BaseModel):
    """Request body for creating a shot with server-side ID generation."""
    scene_description: Optional[str] = ""
    scene_id: Optional[str] = "SCN-001"  # Default scene
    sequence_id: Optional[str] = None  # Legacy support
    status: Optional[str] = "pending"


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


@router.post("/create", response_model=Shot)
async def create_shot_with_server_id(
    request: CreateShotRequest,
    manager: DataManager = Depends(get_data_manager)
):
    """
    Creates a new shot with SERVER-GENERATED ID.
    This endpoint should be used instead of POST / for proper ID generation.
    """
    if not manager.current_project_id:
        raise HTTPException(status_code=400, detail="No project loaded")
    
    # Get existing shot IDs to ensure uniqueness
    existing_shots = manager.get_shots()
    existing_ids = [s.id for s in existing_shots]
    
    # Generate server-side ID
    new_id = id_generator.generate_shot_id(existing_ids)
    
    # Create shot with generated ID
    now = datetime.now().isoformat()
    shot = Shot(
        id=new_id,
        scene_description=request.scene_description,
        sequence_id=request.scene_id,  # Map to legacy field
        status=request.status,
        created_at=now,
        updated_at=now
    )
    
    manager.add_shot(shot)
    logger.info(f"Created shot with server-generated ID: {new_id}")
    
    return shot


@router.post("/{shot_id}/confirm")
async def confirm_shot(
    shot_id: str,
    manager: DataManager = Depends(get_data_manager)
):
    """
    Confirms a shot, locking its folder structure and creating initial versions.
    Once confirmed, the shot's folder structure cannot be changed without explicit unlock.
    """
    if not manager.current_project_id:
        raise HTTPException(status_code=400, detail="No project loaded")
    
    shot = manager.get_shot(shot_id)
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")
    
    # Use scene_id or default to SCN-001
    scene_id = shot.sequence_id or "SCN-001"
    
    # Confirm the shot via filesystem service
    success = manager.fs.confirm_shot(
        manager.current_project_id,
        scene_id,
        shot_id
    )
    
    if success:
        # Update shot status in data
        manager.update_shot(shot_id, {"status": "confirmed"})
        return {"message": f"Shot {shot_id} confirmed", "success": True}
    else:
        raise HTTPException(status_code=500, detail="Failed to confirm shot")

@router.put("/{shot_id}", response_model=Shot)
async def update_shot(shot_id: str, updates: dict, manager: DataManager = Depends(get_data_manager)):
    if not manager.current_project_id:
        raise HTTPException(status_code=400, detail="No project loaded")
    
    updated_shot = manager.update_shot(shot_id, updates)
    if not updated_shot:
        raise HTTPException(status_code=404, detail="Shot not found")
    return updated_shot

@router.post("/reorder", response_model=List[Shot])
async def reorder_shots(shot_ids: List[str], manager: DataManager = Depends(get_data_manager)):
    if not manager.current_project_id:
        raise HTTPException(status_code=400, detail="No project loaded")
    return manager.reorder_shots(shot_ids)

@router.post("/bulk_update")
async def bulk_update_shots(payload: dict, manager: DataManager = Depends(get_data_manager)):
    if not manager.current_project_id:
        raise HTTPException(status_code=400, detail="No project loaded")
    
    ids = payload.get("ids", [])
    updates = payload.get("updates", {})
    
    updated_count = 0
    for shot_id in ids:
        if manager.update_shot(shot_id, updates):
            updated_count += 1
            
    return {"message": "Bulk update successful", "updated_count": updated_count}

@router.get("/export")
async def export_shots(manager: DataManager = Depends(get_data_manager)):
    if not manager.current_project_id:
        raise HTTPException(status_code=400, detail="No project loaded")
    
    import pandas as pd
    import io
    from fastapi.responses import StreamingResponse
    
    shots = manager.get_shots()
    if not shots:
        raise HTTPException(status_code=404, detail="No shots to export")

    # Flatten Data for Export
    export_data = []
    for s in shots:
        row = s.dict()
        
        # Flatten Subjects (Just a summary for now, importing complex lists back is hard in CSV)
        subjects = row.get('subjects', [])
        row['subjects_summary'] = ", ".join([sub.get('character_id', 'Unknown') for sub in subjects]) if subjects else ""
        
        # Flatten Environment
        env = row.get('environment', {}) or {}
        row['env_location'] = env.get('location', '')
        
        # Flatten Technical
        tech = row.get('technical', {}) or {}
        row['tech_camera'] = tech.get('camera', '')
        row['tech_lens'] = tech.get('lens', '')
        row['tech_lighting'] = tech.get('lighting', '')
        
        export_data.append(row)
        
    df = pd.DataFrame(export_data)

    # Select/Order columns for better UX
    cols = ['id', 'scene_description', 'status', 'duration_seconds',
            'subjects_summary', 'env_location', 'tech_camera', 'tech_lens', 'tech_lighting',
            'created_at', 'updated_at']

    # Filter columns that exist
    cols = [c for c in cols if c in df.columns]
    df = df[cols]
    
    stream = io.BytesIO()
    with pd.ExcelWriter(stream, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Shots')
    
    stream.seek(0)
    
    filename = f"{manager.current_project_id}_shots.xlsx"
    headers = {
        'Content-Disposition': f'attachment; filename="{filename}"'
    }
    
    return StreamingResponse(stream, headers=headers, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

from fastapi import UploadFile, File

@router.post("/import")
async def import_shots(file: UploadFile = File(...), manager: DataManager = Depends(get_data_manager)):
    if not manager.current_project_id:
        raise HTTPException(status_code=400, detail="No project loaded")
        
    import pandas as pd
    import io
    
    contents = await file.read()
    try:
        df = pd.read_excel(io.BytesIO(contents))
        df = df.fillna('') # Handle NaN
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid Excel file: {str(e)}")
        
    records = df.to_dict('records')
    updated_count = 0
    created_count = 0
    
    for row in records:
        # Pydantic conversion handles types, but we might need cleanup
        # Character IDs might be string "['A', 'B']" or just "A" in Excel
        if 'character_ids' in row and isinstance(row['character_ids'], str):
            # Very basic cleanup, could be improved
            row['character_ids'] = [row['character_ids']] if row['character_ids'] else []
        elif 'character_ids' not in row:
            row['character_ids'] = []
            
        # Try to find existing shot
        existing = manager.update_shot(row.get('id'), row)
        if existing:
            updated_count += 1
        else:
            # Create new
            try:
                # Ensure required fields
                if 'id' not in row or not row['id']:
                    continue # Skip invalid ID
                
                # Check required fields for model
                if 'scene_description' not in row: row['scene_description'] = ""
                if 'action' not in row: row['action'] = ""
                
                # Add timestamps if missing
                from datetime import datetime
                if 'created_at' not in row or not row['created_at']:
                    row['created_at'] = datetime.now().isoformat()
                row['updated_at'] = datetime.now().isoformat()
                
                shot = Shot(**row)
                manager.add_shot(shot)
                created_count += 1
            except Exception as e:
                logger.warning(f"Skipping row {row.get('id')}: {e}")
                
    return {"message": "Import successful", "updated": updated_count, "created": created_count}

@router.post("/{shot_id}/open_folder")
async def open_shot_folder(shot_id: str, manager: DataManager = Depends(get_data_manager)):
    if not manager.current_project_id:
        raise HTTPException(status_code=400, detail="No project loaded")
    
    shot = manager.get_shot(shot_id)
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")
        
    # Use FileSystemService to get path
    # Default to "working" state and first available task if not specified
    # For now, let's open the shot root
    # We need to construct the path manually or expose a helper in manager/fs
    
    # Quick access via manager.fs
    # Assuming shot_id contains sequence info or we just search.
    # Standard: shots/{sequence}/{shot_id}
    
    seq_id = shot.sequence_id or "SQ01"
    
    # Construct path: projects/{proj}/working/shots/{seq}/{shot}
    # This logic should ideally be in FS service, but accessing it here for speed
    path = manager.fs.get_shot_dir(manager.current_project_id, seq_id, shot_id, task_type="", state="working")
    # Remove terminating task_type separator to get shot root
    # get_shot_dir appends task_type. Let's strip it or adjust the method.
    # Actually get_shot_dir: join(..., task_type). If task_type is empty string...
    
    if not os.path.exists(path):
        # Try creating it if it doesn't exist (safety)
        manager.fs.ensure_shot_structure(manager.current_project_id, seq_id, shot_id)
    
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
        return {"message": f"Opened folder: {path}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to open folder: {str(e)}")

@router.post("/{shot_id}/analyze")
async def analyze_shot(shot_id: str, manager: DataManager = Depends(get_data_manager), analyzer: WorkflowAnalyzer = Depends(get_workflow_analyzer)):
    shot = manager.get_shot(shot_id)
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")
    
    result = analyzer.analyze_shot(shot)
    
    # Optionally verify if we should auto-apply
    return result
