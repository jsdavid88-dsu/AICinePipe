from fastapi import APIRouter

router = APIRouter(
    prefix="/render",
    tags=["render"]
)

@router.post("/batch")
async def start_batch_render():
    return {"status": "started"}
