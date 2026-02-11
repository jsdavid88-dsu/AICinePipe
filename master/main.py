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

from .routers import shots, jobs, workers, websocket, projects, characters, cinematics, cpe

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

# 프로젝트 정적 파일 서빙 (썸네일 등)
os.makedirs(settings.PROJECTS_DIR, exist_ok=True)
app.mount("/projects", StaticFiles(directory=settings.PROJECTS_DIR), name="projects")

# Mount 'ref' directory for cinematic presets images
REF_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ref")
if os.path.exists(REF_DIR):
    app.mount("/ref", StaticFiles(directory=REF_DIR), name="ref")

@app.get("/")
def read_root():
    return {"status": "online", "message": "Master Server is running"}

if __name__ == "__main__":
    uvicorn.run("master.main:app", host="0.0.0.0", port=8002, reload=True)
