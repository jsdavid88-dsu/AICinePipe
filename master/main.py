from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn
import os

# 환경 변수 로드
load_dotenv()

# Logging and config (loguru setup runs on import)
from .utils import logger, settings

logger.info("Starting AI Production Pipeline Master Server...")

from .routers import shots, jobs, workers, websocket, projects, characters, cinematics, cpe, models

app = FastAPI(
    title="AI Production Pipeline Master Server",
    description="Render farm master server for AI video production",
    version="0.1.0"
)

# CORS 설정 - 환경변수 기반
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles

# 라우터 등록
app.include_router(characters.router)
app.include_router(cinematics.router)
app.include_router(projects.router)
app.include_router(shots.router)
app.include_router(jobs.router)
app.include_router(workers.router)
app.include_router(websocket.router)
app.include_router(cpe.router)
app.include_router(models.router)

# 프로젝트 정적 파일 서빙 (썸네일 등)
os.makedirs(settings.PROJECTS_DIR, exist_ok=True)
app.mount("/projects", StaticFiles(directory=settings.PROJECTS_DIR), name="projects")

# Mount 'ref' directory for cinematic presets images
REF_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ref")
if os.path.exists(REF_DIR):
    app.mount("/ref", StaticFiles(directory=REF_DIR), name="ref")

# ── Frontend Static Build Serving ───────────────────────────────────────
# When frontend/dist/ exists (after `npm run build`), serve it directly
# from FastAPI. This means end users don't need Node.js installed.
# In development, the Vite dev server (port 5173) is used instead.

from pathlib import Path
from fastapi.responses import FileResponse

_FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
_FRONTEND_INDEX = _FRONTEND_DIST / "index.html"

if _FRONTEND_DIST.exists() and _FRONTEND_INDEX.exists():
    logger.info(f"Serving frontend from {_FRONTEND_DIST}")

    # Serve static assets (JS, CSS, images) under /assets/
    app.mount("/assets", StaticFiles(directory=str(_FRONTEND_DIST / "assets")), name="frontend_assets")

    # Catch-all: serve index.html for any non-API route (SPA routing)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve the SPA index.html for all non-API routes."""
        # Check if it's a static file in dist/
        file_path = _FRONTEND_DIST / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        # Otherwise serve index.html (React Router handles the path)
        return FileResponse(str(_FRONTEND_INDEX))
else:
    logger.info("Frontend dist/ not found — API-only mode (use Vite dev server)")

    @app.get("/")
    def read_root():
        return {
            "status": "online",
            "message": "Master Server is running",
            "frontend": "Run 'npm run build' in frontend/ to enable built-in UI serving",
        }

if __name__ == "__main__":
    uvicorn.run("master.main:app", host="0.0.0.0", port=8002, reload=True)

