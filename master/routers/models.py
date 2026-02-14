"""
Models Router — Model discovery and management API.

Bridges DSUComfyCG's models_db.json with the pipeline server,
providing REST endpoints for listing, downloading, and managing
AI models used by ComfyUI.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import json
import os
from pathlib import Path

from ..utils import logger, settings

router = APIRouter(prefix="/models", tags=["Models"])

# ── Load Models Database ────────────────────────────────────────────

_CORE_DIR = Path(__file__).resolve().parent.parent.parent / "core"
_MODELS_DB_PATH = _CORE_DIR / "models_db.json"

_models_db: dict = {"models": {}, "folder_mappings": {}}

if _MODELS_DB_PATH.exists():
    with open(_MODELS_DB_PATH, "r", encoding="utf-8") as f:
        _models_db = json.load(f)
    logger.info(f"Loaded models_db: {len(_models_db.get('models', {}))} models")
else:
    logger.warning(f"models_db.json not found at {_MODELS_DB_PATH}")


# ── Helpers ─────────────────────────────────────────────────────────

def _get_comfyui_models_dir() -> Optional[Path]:
    """Find the ComfyUI models directory."""
    comfy_dir = Path(os.getenv("COMFYUI_DIR", ""))
    candidates = [
        comfy_dir / "ComfyUI" / "models",
        comfy_dir / "models",
        Path(settings.PROJECTS_DIR).parent / "comfyui" / "ComfyUI" / "models",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def _is_model_installed(model_name: str) -> bool:
    """Check if a model file exists in ComfyUI models directory."""
    models_dir = _get_comfyui_models_dir()
    if not models_dir:
        return False

    model_info = _models_db.get("models", {}).get(model_name, {})
    folder = model_info.get("folder", "")
    folder_path = _models_db.get("folder_mappings", {}).get(folder, folder)

    # Check relative to ComfyUI base
    comfy_base = models_dir.parent  # ComfyUI/
    full_path = comfy_base / folder_path / model_name
    return full_path.exists()


# ── Response Models ─────────────────────────────────────────────────

class ModelInfo(BaseModel):
    name: str
    repo_id: str
    filename: str
    folder: str
    size: str
    description: str
    installed: bool


class DownloadRequest(BaseModel):
    model_name: str


# ── Endpoints ───────────────────────────────────────────────────────

@router.get("/")
async def list_models():
    """List all known models with their install status."""
    result = []
    for name, info in _models_db.get("models", {}).items():
        result.append(ModelInfo(
            name=name,
            repo_id=info.get("repo_id", ""),
            filename=info.get("filename", ""),
            folder=info.get("folder", ""),
            size=info.get("size", ""),
            description=info.get("description", ""),
            installed=_is_model_installed(name),
        ))
    return {"models": result, "total": len(result)}


@router.get("/installed")
async def list_installed_models():
    """List only installed models (detected from ComfyUI)."""
    all_models = await list_models()
    installed = [m for m in all_models["models"] if m.installed]
    return {"models": installed, "total": len(installed)}


@router.get("/available")
async def list_available_models():
    """List models available for download (not yet installed)."""
    all_models = await list_models()
    available = [m for m in all_models["models"] if not m.installed]
    return {"models": available, "total": len(available)}


@router.get("/comfyui")
async def list_comfyui_resources():
    """
    Query live ComfyUI instance for available models and LoRAs.
    Requires ComfyUI to be running.
    """
    from core.comfy_client import ComfyUIClient

    comfy_url = os.getenv("COMFYUI_URL", "http://127.0.0.1:8188")
    client = ComfyUIClient(comfy_url)

    if not client.is_reachable():
        raise HTTPException(
            status_code=503,
            detail="ComfyUI is not reachable. Start ComfyUI first."
        )

    return {
        "models": client.get_available_models(),
        "loras": client.get_available_loras(),
    }


@router.get("/folder-mappings")
async def get_folder_mappings():
    """Get the model folder type → path mappings."""
    return _models_db.get("folder_mappings", {})


@router.get("/{model_name}")
async def get_model_info(model_name: str):
    """Get detailed info for a specific model."""
    info = _models_db.get("models", {}).get(model_name)
    if not info:
        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found in database")

    return ModelInfo(
        name=model_name,
        repo_id=info.get("repo_id", ""),
        filename=info.get("filename", ""),
        folder=info.get("folder", ""),
        size=info.get("size", ""),
        description=info.get("description", ""),
        installed=_is_model_installed(model_name),
    )
