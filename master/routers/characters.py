from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from ..services.data_manager import DataManager
from ..models.character import Character
from ..dependencies import get_data_manager

router = APIRouter(
    prefix="/characters",
    tags=["characters"]
)

@router.get("/", response_model=List[Character])
async def list_characters(manager: DataManager = Depends(get_data_manager)):
    return manager.get_characters()

@router.post("/", response_model=Character)
async def create_character(character: Character, manager: DataManager = Depends(get_data_manager)):
    try:
        return manager.create_character(character)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Create Failed: {str(e)}")

@router.put("/{character_id}", response_model=Character)
async def update_character(character_id: str, updates: dict, manager: DataManager = Depends(get_data_manager)):
    char = manager.update_character(character_id, updates)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    return char

@router.delete("/{character_id}")
async def delete_character(character_id: str, manager: DataManager = Depends(get_data_manager)):
    success = manager.delete_character(character_id)
    if not success:
        raise HTTPException(status_code=404, detail="Character not found")
    return {"message": "Character deleted"}

from fastapi import UploadFile, File
import os

@router.post("/{character_id}/thumbnail")
async def upload_character_thumbnail(
    character_id: str, 
    file: UploadFile = File(...), 
    manager: DataManager = Depends(get_data_manager)
):
    try:
        project_path = manager._get_project_path(manager.current_project_id)
        if not os.path.exists(project_path):
            raise HTTPException(status_code=400, detail="No project loaded")
            
        # Assets/Characters path
        char_assets_path = os.path.join(project_path, "assets", "characters")
        os.makedirs(char_assets_path, exist_ok=True)
        
        # Save file: Use character_id.png for simplicity, or preserve extension
        # For this "Pro Max" version, let's stick to png/jpg but maybe rename to id
        # EXTENSION CHECK
        ext = os.path.splitext(file.filename)[1]
        if ext.lower() not in ['.png', '.jpg', '.jpeg', '.webp']:
             raise HTTPException(status_code=400, detail="Invalid image format")

        filename = f"{character_id}{ext}"
        file_path = os.path.join(char_assets_path, filename)
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
            
        # Return relative path for frontend
        relative_path = f"/projects/{manager.current_project_id}/assets/characters/{filename}"
        
        # Update character record with thumbnail path?
        # Actually, if we use consistent naming, we might not need to store it, 
        # BUT storing it allows for different extensions and is more robust.
        char = manager.get_character(character_id)
        if char:
            updated_data = char.dict()
            updated_data['thumbnail'] = relative_path
            updated_data['updated_at'] = None # Let update_character handle timestamp
            manager.update_character(character_id, updated_data)
            
        return {"message": "Thumbnail uploaded", "path": relative_path}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
