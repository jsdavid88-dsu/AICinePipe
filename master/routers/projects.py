from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.responses import FileResponse
from typing import List, Dict, Optional
import os
from loguru import logger
from ..dependencies import get_data_manager
from ..services.data_manager import DataManager
from ..services.video_composer import VideoComposer, ComposeOptions, VideoClip

router = APIRouter(
    prefix="/projects",
    tags=["projects"]
)

@router.post("/", status_code=201)
async def create_project(
    project_id: str = Body(..., embed=True), 
    description: str = Body("", embed=True),
    manager: DataManager = Depends(get_data_manager)
):
    try:
        # Validate ID
        import re
        if not re.match(r"^[a-zA-Z0-9_-]+$", project_id):
             raise HTTPException(status_code=400, detail="Invalid project ID. Use alphanumeric, _, - only.")

        logger.debug(f"Creating project: {project_id}")
        success = manager.create_project(project_id)
        if not success:
            raise HTTPException(status_code=409, detail=f"Project {project_id} already exists")
        
        # 메타데이터 저장 (Description 등)
        manager.load_project(project_id)
        
        # Save Description (Quick Hack)
        if description:
            manager._data["description"] = description
            manager.save_project()
        
        return {"message": "Project created", "project_id": project_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Create project failed: {e}")
        raise HTTPException(status_code=500, detail=f"Create Failed: {str(e)}")

from fastapi import UploadFile, File

@router.post("/{project_id}/thumbnail")
async def upload_thumbnail(
    project_id: str, 
    file: UploadFile = File(...), 
    manager: DataManager = Depends(get_data_manager)
):
    try:
        project_path = manager._get_project_path(project_id)
        if not os.path.exists(project_path):
            raise HTTPException(status_code=404, detail="Project not found")
            
        assets_path = os.path.join(project_path, "assets")
        os.makedirs(assets_path, exist_ok=True)
        
        # Save file
        file_path = os.path.join(assets_path, "thumbnail.png") # Force PNG or keep extension
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
            
        return {"message": "Thumbnail uploaded", "path": f"/projects/{project_id}/assets/thumbnail.png"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{project_id}/load")
async def load_project(project_id: str, manager: DataManager = Depends(get_data_manager)):
    try:
        manager.load_project(project_id)
        return {"message": "Project loaded", "project_id": project_id}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Project not found")

@router.get("/")
async def list_projects(manager: DataManager = Depends(get_data_manager)):
    try:
        # projects 폴더 스캔
        if not os.path.exists(manager.projects_root):
            return []
            
        projects = [d for d in os.listdir(manager.projects_root) 
                   if os.path.isdir(os.path.join(manager.projects_root, d))]
        return projects
    except Exception as e:
        logger.exception(f"List projects failed: {e}")
        raise HTTPException(status_code=500, detail=f"List Projects Failed: {str(e)}")


def _frames_to_tc(f: int, fps: int = 24) -> str:
    """Convert frame number to timecode string (HH:MM:SS:FF)."""
    h = int(f / (fps * 3600))
    m = int((f % (fps * 3600)) / (fps * 60))
    s = int((f % (fps * 60)) / fps)
    fr = f % fps
    return f"{h:02d}:{m:02d}:{s:02d}:{fr:02d}"


@router.get("/{project_id}/export/edl")
async def export_edl(project_id: str, manager: DataManager = Depends(get_data_manager)):
    """Export simple CMX3600 style EDL"""
    try:
        manager.load_project(project_id)
        shots = manager.get_shots()
        
        lines = []
        lines.append(f"TITLE: {project_id.upper()}")
        lines.append("FCM: NON-DROP FRAME")
        lines.append("")
        
        current_frame = 0
        for i, shot in enumerate(shots):
            index = f"{i+1:03d}"
            duration_frames = int(shot.duration_seconds * 24)

            src_in = _frames_to_tc(0)
            src_out = _frames_to_tc(duration_frames)
            rec_in = _frames_to_tc(current_frame)
            rec_out = _frames_to_tc(current_frame + duration_frames)
            
            lines.append(f"{index}  AX       V     C        {src_in} {src_out} {rec_in} {rec_out}")
            lines.append(f"* FROM CLIP NAME: {shot.id}")
            lines.append("")
            
            current_frame += duration_frames
            
        content = "\n".join(lines)
        
        from fastapi.responses import Response
        return Response(content=content, media_type="text/plain", headers={
            "Content-Disposition": f"attachment; filename={project_id}.edl"
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"EDL Export Failed: {str(e)}")

@router.get("/{project_id}/archive")
async def archive_project(project_id: str, manager: DataManager = Depends(get_data_manager)):
    """Archive project directory to ZIP"""
    import shutil
    from fastapi.responses import FileResponse
    
    try:
        project_path = manager._get_project_path(project_id)
        if not os.path.exists(project_path):
            raise HTTPException(status_code=404, detail="Project not found")
            
        # Create zip in temp or parent dir
        # For simplicity, store in project parent root
        archive_name = f"{project_id}_archive"
        root_dir = os.path.dirname(project_path)
        base_dir = os.path.basename(project_path)
        
        zip_path = shutil.make_archive(os.path.join(root_dir, archive_name), 'zip', root_dir, base_dir)
        
        return FileResponse(zip_path, filename=f"{project_id}.zip", media_type="application/zip")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Archive Failed: {str(e)}")


# ── Video Composition ──────────────────────────────────────────────────

@router.post("/{project_id}/compose")
async def compose_project(
    project_id: str,
    transition: str = Body("fade", embed=True),
    transition_duration: float = Body(0.5, embed=True),
    manager: DataManager = Depends(get_data_manager)
):
    """Compose all shot videos into a single final video."""
    try:
        manager.load_project(project_id)
        shots = manager.get_shots()

        # Filter shots with video files
        shots_with_video = [s for s in shots if s.generated_video_path and os.path.exists(s.generated_video_path)]

        if not shots_with_video:
            raise HTTPException(status_code=400, detail="No shots have generated videos to compose")

        # Build output path
        project_path = manager._get_project_path(project_id)
        output_dir = os.path.join(project_path, "output")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{project_id}_final.mp4")

        # Build clips from shots
        clips = []
        for shot in shots_with_video:
            clips.append(VideoClip(
                path=shot.generated_video_path,
                duration=shot.duration_seconds,
                transition_type=transition,
                transition_duration=transition_duration,
            ))

        # Compose
        composer = VideoComposer()
        opts = ComposeOptions(output_path=output_path, clips=clips)
        result_path = composer.compose(opts)
        composer.cleanup_temp()

        return {
            "message": "Video composed successfully",
            "output_path": result_path,
            "shots_count": len(shots_with_video),
            "transition": transition,
        }

    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"Compose failed: {e}")
        raise HTTPException(status_code=500, detail=f"Compose Failed: {str(e)}")


@router.get("/{project_id}/compose/download")
async def download_composed_video(
    project_id: str, manager: DataManager = Depends(get_data_manager)
):
    """Download the composed final video if it exists."""
    try:
        project_path = manager._get_project_path(project_id)
        output_path = os.path.join(project_path, "output", f"{project_id}_final.mp4")

        if not os.path.exists(output_path):
            raise HTTPException(status_code=404, detail="No composed video found. Run compose first.")

        return FileResponse(
            output_path,
            filename=f"{project_id}_final.mp4",
            media_type="video/mp4"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download Failed: {str(e)}")
