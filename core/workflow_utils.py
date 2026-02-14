"""
Workflow Utilities
==================
Helpers for manipulating ComfyUI workflow JSON files.

Extracted from MayaAI_Toolkit/engines/comfy.py for shared use by
server, worker, and DCC plugins.
"""

import json
import os
import logging
from typing import Optional

logger = logging.getLogger("core.workflow_utils")


def load_workflow(path: str) -> dict:
    """Load a ComfyUI workflow JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_workflow(workflow: dict, path: str) -> None:
    """Save a workflow dict to JSON file."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)


# ── Node Injection ──────────────────────────────────────────────────

def inject_image(workflow: dict, remote_name: str,
                 node_ids: list = None) -> dict:
    """
    Inject an uploaded image filename into LoadImage nodes.

    Args:
        workflow: ComfyUI workflow dict
        remote_name: Filename as returned by ComfyUIClient.upload_image()
        node_ids: Specific node IDs to inject into. If None, auto-detects
                  all LoadImage nodes.
    """
    if node_ids:
        for nid in node_ids:
            nid = str(nid).strip()
            if nid in workflow:
                workflow[nid]["inputs"]["image"] = remote_name
                logger.debug(f"Injected image → Node {nid}")
    else:
        for node_id, node_data in workflow.items():
            if node_data.get("class_type") == "LoadImage":
                workflow[node_id]["inputs"]["image"] = remote_name
                logger.debug(f"[Auto] Injected image → Node {node_id}")
    return workflow


def inject_mask(workflow: dict, remote_name: str,
                node_id: str = None) -> dict:
    """Inject a mask image into a LoadImage/LoadImageMask node."""
    if node_id and str(node_id) in workflow:
        workflow[str(node_id)]["inputs"]["image"] = remote_name
    else:
        # Auto: second LoadImage or first LoadImageMask
        load_nodes = [
            k for k, v in workflow.items()
            if v.get("class_type") in ("LoadImage", "LoadImageMask")
        ]
        if len(load_nodes) > 1:
            workflow[load_nodes[1]]["inputs"]["image"] = remote_name
    return workflow


def inject_sampler_values(workflow: dict, sampler_id: str = None, *,
                          seed: int = None, steps: int = None,
                          cfg: float = None, denoise: float = None) -> dict:
    """
    Inject seed/steps/cfg/denoise into a KSampler node.

    If sampler_id is None, auto-detects the first KSampler node.
    """
    target_ids = []
    if sampler_id:
        target_ids = [str(sampler_id)]
    else:
        target_ids = [
            nid for nid, nd in workflow.items()
            if "KSampler" in nd.get("class_type", "")
        ]

    for nid in target_ids:
        if nid not in workflow:
            continue
        inputs = workflow[nid]["inputs"]

        if seed is not None:
            for key in ("seed", "noise_seed"):
                if key in inputs:
                    inputs[key] = seed

        if steps is not None and "steps" in inputs:
            inputs["steps"] = steps

        if cfg is not None and "cfg" in inputs:
            inputs["cfg"] = cfg

        if denoise is not None and "denoise" in inputs:
            inputs["denoise"] = denoise

    return workflow


def inject_size(workflow: dict, width: int, height: int,
                size_node_id: str = None) -> dict:
    """Inject width/height into an EmptyLatentImage or similar node."""
    if size_node_id and str(size_node_id) in workflow:
        inputs = workflow[str(size_node_id)]["inputs"]
        if "width" in inputs:
            inputs["width"] = width
        if "height" in inputs:
            inputs["height"] = height
    else:
        for nid, nd in workflow.items():
            if nd.get("class_type") in ("EmptyLatentImage", "EmptySD3LatentImage"):
                nd["inputs"]["width"] = width
                nd["inputs"]["height"] = height
                break
    return workflow


def inject_prompt(workflow: dict, text: str,
                  node_id: str = None) -> dict:
    """Inject text into the first CLIPTextEncode node (positive prompt)."""
    if node_id and str(node_id) in workflow:
        workflow[str(node_id)]["inputs"]["text"] = text
    else:
        for nid, nd in workflow.items():
            if nd.get("class_type") == "CLIPTextEncode":
                if isinstance(nd["inputs"].get("text"), str):
                    nd["inputs"]["text"] = text
                    break
    return workflow


def inject_model(workflow: dict, model_name: str) -> dict:
    """Inject checkpoint name into CheckpointLoaderSimple nodes."""
    for nid, nd in workflow.items():
        if nd.get("class_type") == "CheckpointLoaderSimple":
            nd["inputs"]["ckpt_name"] = model_name
    return workflow


# ── Workflow Analysis ───────────────────────────────────────────────

def get_node_types(workflow: dict) -> dict:
    """Get a summary of node types in the workflow."""
    types = {}
    for nid, nd in workflow.items():
        ct = nd.get("class_type", "Unknown")
        types[ct] = types.get(ct, 0) + 1
    return types


def find_nodes_by_type(workflow: dict, class_type: str) -> list:
    """Find all node IDs matching a given class_type."""
    return [
        nid for nid, nd in workflow.items()
        if nd.get("class_type") == class_type
    ]


def get_output_nodes(workflow: dict) -> list:
    """Find SaveImage/PreviewImage output nodes."""
    output_types = ("SaveImage", "PreviewImage", "SaveAnimatedWEBP", "VHS_VideoCombine")
    return [
        nid for nid, nd in workflow.items()
        if nd.get("class_type") in output_types
    ]
