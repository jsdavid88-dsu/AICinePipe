"""
Parameter Patcher — dynamic parameter substitution in ComfyUI workflows.

Patches workflow JSON with runtime values: prompts, seeds, dimensions,
LoRA settings, filenames, etc. Uses WorkflowParser analysis to know
which nodes serve which roles.
"""

import random
from typing import Any, Optional

from ..utils import logger
from .workflow_parser import WorkflowParser, WorkflowAnalysis


class ParameterPatcher:
    """Patches ComfyUI workflow JSON with dynamic parameters."""

    def __init__(self):
        self._parser = WorkflowParser()

    def patch(
        self,
        workflow_json: dict,
        positive_prompt: str = "",
        negative_prompt: str = "",
        seed: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        steps: Optional[int] = None,
        cfg: Optional[float] = None,
        denoise: Optional[float] = None,
        lora_name: Optional[str] = None,
        lora_strength: Optional[float] = None,
        filename_prefix: Optional[str] = None,
        extra_params: Optional[dict] = None,
    ) -> dict:
        """
        Patch a workflow with runtime parameters.
        Returns the patched workflow (modifies in place).
        """
        analysis = self._parser.analyze(workflow_json)

        if analysis.errors:
            logger.warning(f"Workflow analysis errors: {analysis.errors}")

        # Patch positive prompts
        if positive_prompt:
            for node_id in analysis.positive_prompt_nodes:
                node = workflow_json.get(node_id, {})
                inputs = node.get("inputs", {})
                if "text" in inputs:
                    inputs["text"] = positive_prompt
                    logger.debug(f"Patched positive prompt on node {node_id}")

        # Patch negative prompts
        if negative_prompt:
            for node_id in analysis.negative_prompt_nodes:
                node = workflow_json.get(node_id, {})
                inputs = node.get("inputs", {})
                if "text" in inputs:
                    inputs["text"] = negative_prompt
                    logger.debug(f"Patched negative prompt on node {node_id}")

        # Patch sampler parameters
        for node_id in analysis.sampler_nodes:
            node = workflow_json.get(node_id, {})
            inputs = node.get("inputs", {})

            if seed is not None:
                inputs["seed"] = seed
            elif "seed" in inputs:
                # Randomize seed if not specified
                inputs["seed"] = random.randint(0, 2**32 - 1)

            if steps is not None and "steps" in inputs:
                inputs["steps"] = steps
            if cfg is not None and "cfg" in inputs:
                inputs["cfg"] = cfg
            if denoise is not None and "denoise" in inputs:
                inputs["denoise"] = denoise

        # Patch dimensions (find EmptyLatentImage or similar)
        if width is not None or height is not None:
            for param in analysis.parameters:
                if param.role == "width" and width:
                    node = workflow_json.get(param.node_id, {})
                    node.get("inputs", {})[param.param_name] = width
                elif param.role == "height" and height:
                    node = workflow_json.get(param.node_id, {})
                    node.get("inputs", {})[param.param_name] = height

        # Patch LoRA
        if lora_name:
            for node_id in analysis.lora_nodes:
                node = workflow_json.get(node_id, {})
                inputs = node.get("inputs", {})
                inputs["lora_name"] = lora_name
                if lora_strength is not None:
                    inputs["strength_model"] = lora_strength
                    inputs["strength_clip"] = lora_strength
                logger.debug(f"Patched LoRA on node {node_id}: {lora_name}")

        # Patch filename prefix
        if filename_prefix:
            for node_id in analysis.save_nodes:
                node = workflow_json.get(node_id, {})
                inputs = node.get("inputs", {})
                if "filename_prefix" in inputs:
                    inputs["filename_prefix"] = filename_prefix

        # Apply extra params (node_id -> {param_name: value})
        if extra_params:
            for node_id, params in extra_params.items():
                node = workflow_json.get(node_id, {})
                inputs = node.get("inputs", {})
                for key, value in params.items():
                    inputs[key] = value

        logger.info(
            f"Workflow patched: prompts={'✓' if positive_prompt else '✗'}, "
            f"seed={seed or 'random'}, "
            f"lora={'✓' if lora_name else '✗'}"
        )
        return workflow_json
