from fastapi import APIRouter
from typing import List
from ..models.worker import WorkerNode

router = APIRouter(
    prefix="/workers",
    tags=["workers"]
)

@router.get("/", response_model=List[WorkerNode])
async def get_workers():
    return []

@router.post("/register", response_model=WorkerNode)
async def register_worker(worker: WorkerNode):
    return worker
