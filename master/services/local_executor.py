import json
import os
import requests
import asyncio
from loguru import logger
from ..models.job import Job, JobStatus

class LocalExecutor:
    def __init__(self, comfy_url="http://127.0.0.1:8188", workflow_dir="workflows"):
        self.comfy_url = comfy_url
        self.workflow_dir = workflow_dir

    def execute_job(self, job: Job):
        """
        로컬 ComfyUI에 작업을 바로 큐잉합니다.
        """
        logger.info(f"Executing Job {job.id} ({job.workflow_type})...")
        
        # 1. 템플릿 로드
        # workflow_type 예: "text_to_image/flux_basic"
        template_path = os.path.join(self.workflow_dir, f"{job.workflow_type}.json")
        if not os.path.exists(template_path):
            logger.error(f"Workflow template not found at {template_path}")
            return False

        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                workflow = json.load(f)
        except Exception as e:
            logger.error(f"Error loading template: {e}")
            return False

        # 2. 파라미터 주입
        self._inject_params(workflow, job.params)

        # 3. Queue Prompt
        try:
            p = {"prompt": workflow, "client_id": "master_server_local"}
            resp = requests.post(f"{self.comfy_url}/prompt", json=p)
            resp.raise_for_status()
            res_json = resp.json()
            logger.info(f"Job {job.id} queued successfully. PID: {res_json.get('prompt_id')}")
            return True
        except Exception as e:
            logger.error(f"Failed to queue prompt: {e}")
            return False

    def _inject_params(self, workflow, params):
        # 간단한 파라미터 주입 로직 (Worker와 동일)
        seed = params.get("seed", 7777777)
        prompt = params.get("prompt", "")
        
        for node_id, node in workflow.items():
            class_type = node.get("class_type", "")
            inputs = node.get("inputs", {})
            
            if "KSampler" in class_type or "Seed" in class_type:
                if "seed" in inputs: inputs["seed"] = seed
                if "noise_seed" in inputs: inputs["noise_seed"] = seed
            
            if class_type == "CLIPTextEncode":
                # 긍정 프롬프트 (임시: 모든 텍스트 노드에 주입)
                if isinstance(inputs.get("text"), str):
                    inputs["text"] = prompt
            
            if class_type == "CheckpointLoaderSimple" and "ckpt_name" in params:
                 inputs["ckpt_name"] = params["ckpt_name"]
