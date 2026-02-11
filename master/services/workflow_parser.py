"""
Workflow Parser — analyzes ComfyUI workflow JSON to identify editable parameters.

Key capability: distinguishes positive vs negative prompt nodes by tracing
connections from CLIPTextEncode to KSampler's positive/negative inputs.
This resolves the critical issue where both prompts received identical content.
"""

import json
from pathlib import Path
from typing import Any, Optional

from ..utils import logger


# Node types that contain text prompts
PROMPT_NODE_TYPES = {"CLIPTextEncode", "CLIPTextEncodeSDXL"}

# Node types that are samplers (have positive/negative inputs)
SAMPLER_NODE_TYPES = {
    "KSampler", "KSamplerAdvanced", "SamplerCustom",
    "KSampler (Efficient)", "Eff. Loader SDXL",
}

# Node types for LoRA loading
LORA_NODE_TYPES = {"LoraLoader", "LoraLoaderModelOnly", "Power Lora Loader (rgthree)"}

# Node types for image loading
IMAGE_LOAD_TYPES = {"LoadImage", "LoadImageMask"}

# Node types for saving
SAVE_NODE_TYPES = {"SaveImage", "PreviewImage", "SaveAnimatedWEBP"}


class WorkflowParameter:
    """A discovered editable parameter in a workflow."""

    def __init__(
        self,
        node_id: str,
        node_type: str,
        param_name: str,
        current_value: Any,
        role: str = "unknown",
        description: str = "",
    ):
        self.node_id = node_id
        self.node_type = node_type
        self.param_name = param_name
        self.current_value = current_value
        self.role = role  # "positive_prompt", "negative_prompt", "seed", "width", etc.
        self.description = description

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "param_name": self.param_name,
            "current_value": self.current_value,
            "role": self.role,
            "description": self.description,
        }


class WorkflowAnalysis:
    """Result of analyzing a ComfyUI workflow."""

    def __init__(self):
        self.parameters: list[WorkflowParameter] = []
        self.positive_prompt_nodes: list[str] = []  # node IDs
        self.negative_prompt_nodes: list[str] = []  # node IDs
        self.sampler_nodes: list[str] = []
        self.lora_nodes: list[str] = []
        self.save_nodes: list[str] = []
        self.image_load_nodes: list[str] = []
        self.errors: list[str] = []

    def to_dict(self) -> dict:
        return {
            "parameters": [p.to_dict() for p in self.parameters],
            "positive_prompt_nodes": self.positive_prompt_nodes,
            "negative_prompt_nodes": self.negative_prompt_nodes,
            "sampler_nodes": self.sampler_nodes,
            "lora_nodes": self.lora_nodes,
            "save_nodes": self.save_nodes,
            "image_load_nodes": self.image_load_nodes,
            "errors": self.errors,
        }


class WorkflowParser:
    """Parses ComfyUI workflow JSON to extract editable parameters."""

    def analyze(self, workflow_json: dict) -> WorkflowAnalysis:
        """Analyze a ComfyUI API-format workflow JSON."""
        analysis = WorkflowAnalysis()

        if not workflow_json:
            analysis.errors.append("Empty workflow JSON")
            return analysis

        # Phase 1: Identify all node types
        for node_id, node_data in workflow_json.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")
            inputs = node_data.get("inputs", {})

            # Classify nodes
            if class_type in SAMPLER_NODE_TYPES:
                analysis.sampler_nodes.append(node_id)
            elif class_type in LORA_NODE_TYPES:
                analysis.lora_nodes.append(node_id)
            elif class_type in SAVE_NODE_TYPES:
                analysis.save_nodes.append(node_id)
            elif class_type in IMAGE_LOAD_TYPES:
                analysis.image_load_nodes.append(node_id)

        # Phase 2: Trace prompt connections to determine positive/negative
        prompt_roles = self._trace_prompt_roles(workflow_json, analysis.sampler_nodes)

        # Phase 3: Extract editable parameters
        for node_id, node_data in workflow_json.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")
            inputs = node_data.get("inputs", {})

            # Extract prompt parameters
            if class_type in PROMPT_NODE_TYPES:
                role = prompt_roles.get(node_id, "unknown_prompt")
                if role == "positive":
                    analysis.positive_prompt_nodes.append(node_id)
                elif role == "negative":
                    analysis.negative_prompt_nodes.append(node_id)

                text_value = inputs.get("text", "")
                # Only add if it's a direct value, not a link
                if isinstance(text_value, str):
                    analysis.parameters.append(WorkflowParameter(
                        node_id=node_id,
                        node_type=class_type,
                        param_name="text",
                        current_value=text_value,
                        role=f"{role}_prompt",
                        description=f"{role.capitalize()} prompt text",
                    ))

            # Extract sampler parameters
            if class_type in SAMPLER_NODE_TYPES:
                for param in ["seed", "steps", "cfg", "denoise"]:
                    if param in inputs and isinstance(inputs[param], (int, float)):
                        analysis.parameters.append(WorkflowParameter(
                            node_id=node_id,
                            node_type=class_type,
                            param_name=param,
                            current_value=inputs[param],
                            role=param,
                            description=f"Sampler {param}",
                        ))

                # Width/Height from latent
                if "latent_image" in inputs and isinstance(inputs["latent_image"], list):
                    latent_id = str(inputs["latent_image"][0])
                    latent_node = workflow_json.get(latent_id, {})
                    latent_inputs = latent_node.get("inputs", {})
                    for dim in ["width", "height"]:
                        if dim in latent_inputs and isinstance(latent_inputs[dim], int):
                            analysis.parameters.append(WorkflowParameter(
                                node_id=latent_id,
                                node_type=latent_node.get("class_type", ""),
                                param_name=dim,
                                current_value=latent_inputs[dim],
                                role=dim,
                                description=f"Image {dim}",
                            ))

            # Extract LoRA parameters
            if class_type in LORA_NODE_TYPES:
                for param in ["lora_name", "strength_model", "strength_clip"]:
                    if param in inputs:
                        val = inputs[param]
                        if not isinstance(val, list):
                            analysis.parameters.append(WorkflowParameter(
                                node_id=node_id,
                                node_type=class_type,
                                param_name=param,
                                current_value=val,
                                role=f"lora_{param}",
                                description=f"LoRA {param}",
                            ))

            # Extract save filename prefix
            if class_type in SAVE_NODE_TYPES:
                if "filename_prefix" in inputs:
                    analysis.parameters.append(WorkflowParameter(
                        node_id=node_id,
                        node_type=class_type,
                        param_name="filename_prefix",
                        current_value=inputs["filename_prefix"],
                        role="filename_prefix",
                        description="Output filename prefix",
                    ))

        logger.info(
            f"Workflow analysis: {len(analysis.parameters)} params, "
            f"{len(analysis.positive_prompt_nodes)} positive, "
            f"{len(analysis.negative_prompt_nodes)} negative prompts"
        )
        return analysis

    def _trace_prompt_roles(
        self, workflow: dict, sampler_ids: list[str]
    ) -> dict[str, str]:
        """
        Trace connections backwards from KSampler inputs to determine
        which CLIPTextEncode nodes are positive vs negative.

        Returns: {node_id: "positive" | "negative"}
        """
        roles: dict[str, str] = {}

        for sampler_id in sampler_ids:
            sampler = workflow.get(sampler_id, {})
            inputs = sampler.get("inputs", {})

            # KSampler has "positive" and "negative" input slots
            positive_input = inputs.get("positive")
            negative_input = inputs.get("negative")

            # Trace positive chain
            if isinstance(positive_input, list) and len(positive_input) >= 1:
                pos_source = str(positive_input[0])
                prompt_id = self._trace_to_prompt(workflow, pos_source)
                if prompt_id:
                    roles[prompt_id] = "positive"

            # Trace negative chain
            if isinstance(negative_input, list) and len(negative_input) >= 1:
                neg_source = str(negative_input[0])
                prompt_id = self._trace_to_prompt(workflow, neg_source)
                if prompt_id:
                    roles[prompt_id] = "negative"

        return roles

    def _trace_to_prompt(
        self, workflow: dict, node_id: str, depth: int = 0
    ) -> Optional[str]:
        """
        Trace from a node backwards through the graph to find a
        CLIPTextEncode node. Handles intermediate nodes like
        ConditioningCombine, LoraLoader, etc.
        """
        if depth > 10:  # Prevent infinite loops
            return None

        node = workflow.get(node_id, {})
        class_type = node.get("class_type", "")

        # Found a prompt node
        if class_type in PROMPT_NODE_TYPES:
            return node_id

        # If it's a conditioning combiner, trace its first input
        inputs = node.get("inputs", {})
        for key in ["conditioning", "conditioning_1", "cond"]:
            val = inputs.get(key)
            if isinstance(val, list) and len(val) >= 1:
                result = self._trace_to_prompt(workflow, str(val[0]), depth + 1)
                if result:
                    return result

        return None

    def analyze_file(self, filepath: str | Path) -> WorkflowAnalysis:
        """Analyze a workflow from a JSON file."""
        path = Path(filepath)
        if not path.exists():
            analysis = WorkflowAnalysis()
            analysis.errors.append(f"File not found: {filepath}")
            return analysis

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return self.analyze(data)
        except json.JSONDecodeError as e:
            analysis = WorkflowAnalysis()
            analysis.errors.append(f"Invalid JSON: {e}")
            return analysis
