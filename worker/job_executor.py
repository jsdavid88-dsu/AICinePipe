import json
import os
import random
from comfy_client import ComfyClient

class JobExecutor:
    def __init__(self, comfy_client: ComfyClient, workflow_dir: str = "../workflows"):
        self.client = comfy_client
        self.workflow_dir = workflow_dir

    def execute_job(self, job_data: dict, client_id: str):
        # 1. 템플릿 로드
        workflow_type = job_data.get("workflow_type", "text_to_image/flux_basic")
        template_path = os.path.join(self.workflow_dir, f"{workflow_type}.json")
        
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Workflow template not found: {template_path}")
            
        with open(template_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
            
        # 2. 파라미터 주입 (간단한 매핑 로직)
        params = job_data.get("params", {})
        self._inject_params(workflow, params)
        
        # 3. 실행 요청
        print(f"Queuing prompt for job {job_data.get('id')}...")
        try:
            resp = self.client.queue_prompt(workflow, client_id)
            prompt_id = resp.get("prompt_id")
            return prompt_id
        except Exception as e:
            print(f"Failed to queue prompt: {e}")
            raise

    def _inject_params(self, workflow, params):
        # ComfyUI API Format: "NodeID": { "inputs": { ... }, "class_type": ... }
        # 템플릿 구조에 따라 파싱. 여기서는 'prompt' 키워드를 찾아서 주입하는 단순 로직 예시
        
        positive_prompt = params.get("prompt", "")
        seed = params.get("seed", random.randint(0, 1000000000))
        
        for node_id, node in workflow.items():
            class_type = node.get("class_type", "")
            inputs = node.get("inputs", {})
            
            # KSampler Seed
            if "KSampler" in class_type or "Seed" in class_type:
                if "seed" in inputs:
                    inputs["seed"] = seed
                if "noise_seed" in inputs:
                    inputs["noise_seed"] = seed

            # Text Prompts (Primitive 방식, 노드 타이틀이나 클래스로 구분 필요)
            # 여기서는 편의상 inputs에 'text'가 있고, CLIPTextEncode 인 경우를 찾음
            if class_type == "CLIPTextEncode":
                # 긍정 프롬프트 (Node Title이나 ID로 구분해야 완벽하지만, 일단 첫번째/두번째 구분 없이 다 넣음 -> 개선 필요)
                # 실제로는 템플릿의 특정 노드 ID를 고정해서 쓰는게 좋음 (ex: Node 6 is Positive, Node 7 is Negative)
                if isinstance(inputs.get("text"), str):
                     # 임시: 모든 텍스트 인코더에 같은 프롬프트 넣음 (테스트용)
                     # TODO: Implement Node ID mapping from params
                    inputs["text"] = positive_prompt
                    
            # Checkpoint Loader
            if class_type == "CheckpointLoaderSimple":
                if "ckpt_name" in params:
                    inputs["ckpt_name"] = params["ckpt_name"]

        return workflow
