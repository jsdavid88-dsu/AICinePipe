from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Optional
from loguru import logger
from ..dependencies import get_job_manager, get_local_executor
from ..services.job_manager import JobManager
from ..services.prompt_engine import PromptEngine
from ..models.job import Job, JobStatus

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"]
)

@router.get("/", response_model=List[Job])
async def list_jobs(project_id: Optional[str] = None, manager: JobManager = Depends(get_job_manager)):
    return manager.list_jobs(project_id)

@router.post("/", response_model=Job)
async def create_job(
    project_id: str = Body(...),
    shot_id: str = Body(...),
    workflow_type: str = Body(...),
    params: dict = Body(...),
    manager: JobManager = Depends(get_job_manager),
    local_exec: object = Depends(get_local_executor) # Type hint simplified
):
    try:
        from ..websocket.connection_manager import manager as ws_manager
        
        # 0. Assemble Prompt from Shot Data
        # Retrieve Shot & Characters
        data_mgr = manager.data_manager
        shot = data_mgr.get_shot(shot_id)
        if not shot:
            raise HTTPException(status_code=404, detail=f"Shot {shot_id} not found")
            
        relevant_chars = []
        for subject in shot.subjects:
            char = data_mgr.get_character(subject.character_id)
            if char: relevant_chars.append(char)
            
        # Assemble Prompt
        generated_prompt = PromptEngine.assemble_prompt(shot, relevant_chars)
        
        # Inject into params (Prepend if user provided one, or overwrite)
        user_prompt = params.get("prompt", "")
        if user_prompt:
            combined_prompt = f"{generated_prompt}, {user_prompt}"
        else:
            combined_prompt = generated_prompt
            
        params["prompt"] = combined_prompt
        
        # Inject LoRA params if needed? (PromptEngine can return lora config, but we need to inject into params for executor)
        # For now, let's assume LoRA mapping is handled by workflow or specialized PromptEngine method
        # PromptEngine.get_lora_config(relevant_chars) -> could be added to params["loras"] 
        # But LocalExecutor needs to know how to handle it. Phase 4 stuff.
        # For Phase 3, prompt text is key.
        
        # 1. Create Job Record
        job = manager.create_job(project_id, shot_id, workflow_type, params)
        
        # 2. Scheduling: Try Worker First
        # Simple Logic: Get first idle worker (not implemented strictly, just broadcast for now or pick random)
        # TODO: Implement proper scheduler in Phase 6
        
        worker_found = False
        if ws_manager.active_connections:
            # Pick first available worker
            worker_id = list(ws_manager.active_connections.keys())[0]
            logger.info(f"Dispatching job {job.id} to worker {worker_id}")
            
            await ws_manager.send_personal_message({
                "type": "job_assign",
                "job": job.dict(),
                "job_id": job.id
            }, worker_id)
            
            manager.update_job_status(job.id, JobStatus.ASSIGNED)
            worker_found = True
        
        # 3. Fallback: Local Execution
        if not worker_found:
            logger.warning("No workers available. Attempting local execution...")
            success = local_exec.execute_job(job)
            if success:
                manager.update_job_status(job.id, JobStatus.RUNNING, "Started locally")
            else:
                 manager.update_job_status(job.id, JobStatus.FAILED, "Local execution failed")
                 
        return job
    except Exception as e:
        logger.exception(f"Job creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{job_id}", response_model=Job)
async def get_job(job_id: str, manager: JobManager = Depends(get_job_manager)):
    job = manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.post("/{job_id}/cancel")
async def cancel_job(job_id: str, manager: JobManager = Depends(get_job_manager)):
    manager.update_job_status(job_id, JobStatus.CANCELLED)
    return {"message": "Job cancelled"}
