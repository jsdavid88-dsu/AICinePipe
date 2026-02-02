from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn
import os

# 환경 변수 로드
load_dotenv()

from .routers import shots, projects, jobs, websocket

app = FastAPI(
    title="AI Production Pipeline Master Server",
    description="Render farm master server for AI video production",
    version="0.1.0"
)

# CORS 설정
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "*"  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(projects.router)
app.include_router(shots.router)
app.include_router(jobs.router)
app.include_router(websocket.router)

@app.get("/")
def read_root():
    return {"status": "online", "message": "Master Server is running"}

if __name__ == "__main__":
    uvicorn.run("master.main:app", host="0.0.0.0", port=8002, reload=True)
