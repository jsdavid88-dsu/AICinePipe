import json
import os
import random
from comfy_client import ComfyClient

try:
    # Available when worker is co-located with master (dev mode)
    from master.services.parameter_patcher import ParameterPatcher
    _patcher = ParameterPatcher()
    _HAS_PATCHER = True
except ImportError:
    _patcher = None
    _HAS_PATCHER = False


class JobExecutor:
    def __init__(self, comfy_client: ComfyClient, workflow_dir: str = "../workflows"):
        self.client = comfy_client
        self.workflow_dir = workflow_dir

    def execute_job(self, job_data: dict, client_id: str):
        # 1. Load workflow template
        workflow_type = job_data.get("workflow_type", "text_to_image/flux_basic")
        template_path = os.path.join(self.workflow_dir, f"{workflow_type}.json")

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Workflow template not found: {template_path}")

        with open(template_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)

        # 2. Inject parameters using ParameterPatcher (connection-aware)
        params = job_data.get("params", {})
        self._inject_params(workflow, params)

        # 3. Queue prompt
        print(f"Queuing prompt for job {job_data.get('id')}...")
        try:
            resp = self.client.queue_prompt(workflow, client_id)
            prompt_id = resp.get("prompt_id")
            return prompt_id
        except Exception as e:
            print(f"Failed to queue prompt: {e}")
            raise

    def _inject_params(self, workflow, params):
        """
        Inject runtime parameters into a ComfyUI workflow.

        Uses ParameterPatcher which traces KSampler connections to correctly
        route positive and negative prompts to the right CLIPTextEncode nodes.
        Falls back to legacy node-ID-based injection if patcher unavailable.
        """
        if _HAS_PATCHER:
            _patcher.patch(
                workflow,
                positive_prompt=params.get("prompt", ""),
                negative_prompt=params.get("negative_prompt", ""),
                seed=params.get("seed"),
                width=params.get("width"),
                height=params.get("height"),
                steps=params.get("steps"),
                cfg=params.get("cfg"),
                denoise=params.get("denoise"),
                lora_name=params.get("lora_name"),
                lora_strength=params.get("lora_strength"),
                filename_prefix=params.get("filename_prefix"),
            )
        else:
            # Legacy fallback: basic node-type matching
            self._inject_params_legacy(workflow, params)

        return workflow

    def _inject_params_legacy(self, workflow, params):
        """Legacy parameter injection (no connection tracing)."""
        positive_prompt = params.get("prompt", "")
        negative_prompt = params.get("negative_prompt", "")
        seed = params.get("seed", random.randint(0, 1000000000))

        prompt_nodes_found = []

        for node_id, node in workflow.items():
            class_type = node.get("class_type", "")
            inputs = node.get("inputs", {})

            # KSampler Seed
            if "KSampler" in class_type or "Seed" in class_type:
                if "seed" in inputs:
                    inputs["seed"] = seed
                if "noise_seed" in inputs:
                    inputs["noise_seed"] = seed

            # CLIPTextEncode — collect for ordered assignment
            if class_type == "CLIPTextEncode" and isinstance(inputs.get("text"), str):
                prompt_nodes_found.append((node_id, inputs))

            # Checkpoint Loader
            if class_type == "CheckpointLoaderSimple":
                if "ckpt_name" in params:
                    inputs["ckpt_name"] = params["ckpt_name"]

        # Assign prompts: first text node = positive, second = negative
        if len(prompt_nodes_found) >= 1 and positive_prompt:
            prompt_nodes_found[0][1]["text"] = positive_prompt
        if len(prompt_nodes_found) >= 2 and negative_prompt:
            prompt_nodes_found[1][1]["text"] = negative_prompt
