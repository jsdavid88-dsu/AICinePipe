"""
Unified ComfyUI Client
======================
Merges functionality from:
  - worker/comfy_client.py (basic prompt queueing, history polling)
  - MayaAI_Toolkit/engines/comfy.py (image upload, workflow injection, completion wait)

Used by both the Worker agent and DCC bridge plugins.

Usage:
    client = ComfyUIClient("http://127.0.0.1:8188")

    # Simple: queue a workflow
    result = client.queue_prompt(workflow)

    # Full: upload image → inject → queue → wait → download
    client.upload_image("input.png", "maya_input.png")
    client.inject_image(workflow, "maya_input.png")
    prompt_id = client.queue_prompt(workflow)
    result_path = client.wait_and_download(prompt_id, "./output")
"""

import json
import os
import time
import uuid
import logging
from pathlib import Path
from typing import Optional, Callable

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import urllib.request
    import urllib.error
    HAS_URLLIB = True
except ImportError:
    HAS_URLLIB = False

logger = logging.getLogger("core.comfy_client")


class ComfyUIClient:
    """
    Unified client for ComfyUI HTTP API.

    Supports both `requests` (preferred) and `urllib` (fallback for
    environments like Maya where requests may not be available).
    """

    def __init__(self, base_url: str = "http://127.0.0.1:8188"):
        self.base_url = base_url.rstrip("/")
        self.client_id = str(uuid.uuid4())

    # ── Health Check ────────────────────────────────────────────────

    def is_reachable(self, timeout: float = 2.0) -> bool:
        """Check if ComfyUI server is reachable."""
        try:
            self._get("/system_stats", timeout=timeout)
            return True
        except Exception:
            return False

    def get_system_stats(self) -> dict:
        """Get ComfyUI system statistics (GPU, memory, etc.)."""
        return self._get("/system_stats")

    # ── Prompt Queue ────────────────────────────────────────────────

    def queue_prompt(self, workflow: dict) -> dict:
        """
        Submit a workflow to ComfyUI for execution.

        Returns:
            dict with 'prompt_id' and other queue info
        """
        payload = {
            "prompt": workflow,
            "client_id": self.client_id,
        }
        return self._post("/prompt", payload)

    # ── History ─────────────────────────────────────────────────────

    def get_history(self, prompt_id: str) -> dict:
        """Get execution history for a specific prompt."""
        return self._get(f"/history/{prompt_id}")

    def get_queue(self) -> dict:
        """Get current queue status."""
        return self._get("/queue")

    # ── Image Upload ────────────────────────────────────────────────

    def upload_image(self, local_path: str, remote_name: str = None) -> str:
        """
        Upload an image to ComfyUI input folder.

        Args:
            local_path: Path to local image file
            remote_name: Name to use on server (default: original filename)

        Returns:
            Remote filename as stored by ComfyUI
        """
        if remote_name is None:
            remote_name = os.path.basename(local_path)

        with open(local_path, "rb") as f:
            image_data = f.read()

        # Use multipart upload
        boundary = "----WebKitFormBoundaryComfyClient"
        body = b"\r\n".join([
            f"--{boundary}".encode(),
            f'Content-Disposition: form-data; name="image"; filename="{remote_name}"'.encode(),
            b"Content-Type: image/png",
            b"",
            image_data,
            f"--{boundary}--".encode(),
            b"",
        ])

        if HAS_REQUESTS:
            # requests-based upload (simpler)
            files = {"image": (remote_name, open(local_path, "rb"), "image/png")}
            resp = requests.post(f"{self.base_url}/upload/image", files=files)
            resp.raise_for_status()
            return resp.json()["name"]
        else:
            # urllib fallback (for Maya / embedded Python)
            req = urllib.request.Request(
                f"{self.base_url}/upload/image",
                data=body,
            )
            req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
            with urllib.request.urlopen(req) as res:
                return json.loads(res.read().decode())["name"]

    # ── Image Download ──────────────────────────────────────────────

    def get_image_url(self, filename: str, subfolder: str = "", img_type: str = "output") -> str:
        """Get the URL for viewing/downloading an image from ComfyUI."""
        return f"{self.base_url}/view?filename={filename}&subfolder={subfolder}&type={img_type}"

    def download_image(self, filename: str, save_path: str,
                       subfolder: str = "", img_type: str = "output") -> str:
        """
        Download an image from ComfyUI to local path.

        Returns:
            Local path where image was saved
        """
        url = self.get_image_url(filename, subfolder, img_type)

        os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)

        if HAS_REQUESTS:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            with open(save_path, "wb") as f:
                f.write(resp.content)
        else:
            with urllib.request.urlopen(url) as res:
                with open(save_path, "wb") as f:
                    f.write(res.read())

        return save_path

    # ── Completion Polling ──────────────────────────────────────────

    def wait_for_completion(
        self,
        prompt_id: str,
        timeout: float = 600.0,
        poll_interval: float = 1.0,
        status_callback: Optional[Callable[[str], None]] = None,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> dict:
        """
        Poll history until prompt completes or fails.

        Args:
            prompt_id: The prompt ID from queue_prompt()
            timeout: Max wait time in seconds
            poll_interval: Seconds between polls
            status_callback: Optional fn(status_str) for progress updates
            progress_callback: Optional fn(percent_int) for progress bar

        Returns:
            dict with 'outputs' containing result images/data

        Raises:
            TimeoutError: If timeout exceeded
        """
        elapsed = 0.0

        while elapsed < timeout:
            time.sleep(poll_interval)
            elapsed += poll_interval

            try:
                history = self.get_history(prompt_id)

                if prompt_id in history:
                    result = history[prompt_id]

                    # Check for errors
                    status_info = result.get("status", {})
                    if status_info.get("status_str") == "error":
                        error_msgs = status_info.get("messages", [])
                        raise RuntimeError(f"ComfyUI execution error: {error_msgs}")

                    outputs = result.get("outputs", {})
                    if outputs:
                        if progress_callback:
                            progress_callback(100)
                        return result

            except (ConnectionError, OSError) as e:
                if status_callback:
                    status_callback(f"Connection issue: {str(e)[:40]}...")

            remaining = int(timeout - elapsed)
            if status_callback:
                status_callback(f"Rendering... ({remaining}s remaining)")

        raise TimeoutError(f"ComfyUI render timeout ({timeout}s)")

    def wait_and_download(
        self,
        prompt_id: str,
        save_dir: str,
        timeout: float = 600.0,
        status_callback: Optional[Callable] = None,
        progress_callback: Optional[Callable] = None,
    ) -> Optional[str]:
        """
        Wait for completion and download the first output image.

        Returns:
            Path to downloaded image, or None if no images in output
        """
        result = self.wait_for_completion(
            prompt_id, timeout, status_callback=status_callback,
            progress_callback=progress_callback,
        )

        outputs = result.get("outputs", {})
        for node_id, node_output in outputs.items():
            images = node_output.get("images", [])
            if images:
                img = images[0]
                filename = img["filename"]
                subfolder = img.get("subfolder", "")

                os.makedirs(save_dir, exist_ok=True)
                local_name = f"output_{int(time.time())}_{filename}"
                local_path = os.path.join(save_dir, local_name)

                return self.download_image(filename, local_path, subfolder)

        return None

    # ── Resource Discovery ──────────────────────────────────────────

    def get_available_models(self) -> list:
        """Get list of checkpoint models available on ComfyUI server."""
        try:
            data = self._get("/object_info/CheckpointLoaderSimple")
            return (
                data.get("CheckpointLoaderSimple", {})
                .get("input", {})
                .get("required", {})
                .get("ckpt_name", [[]])[0]
            )
        except Exception as e:
            logger.warning(f"Failed to fetch models: {e}")
            return []

    def get_available_loras(self) -> list:
        """Get list of LoRA files available on ComfyUI server."""
        try:
            data = self._get("/object_info/LoraLoader")
            return (
                data.get("LoraLoader", {})
                .get("input", {})
                .get("required", {})
                .get("lora_name", [[]])[0]
            )
        except Exception as e:
            logger.warning(f"Failed to fetch LoRAs: {e}")
            return []

    def get_object_info(self, node_type: str = None) -> dict:
        """Get ComfyUI node type info. If node_type is None, returns all."""
        path = f"/object_info/{node_type}" if node_type else "/object_info"
        return self._get(path)

    # ── Internal HTTP Methods ───────────────────────────────────────

    def _get(self, path: str, timeout: float = 10.0) -> dict:
        """HTTP GET with automatic library selection."""
        url = f"{self.base_url}{path}"

        if HAS_REQUESTS:
            resp = requests.get(url, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        else:
            with urllib.request.urlopen(url, timeout=timeout) as res:
                return json.loads(res.read().decode())

    def _post(self, path: str, data: dict, timeout: float = 30.0) -> dict:
        """HTTP POST JSON with automatic library selection."""
        url = f"{self.base_url}{path}"

        if HAS_REQUESTS:
            resp = requests.post(url, json=data, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        else:
            json_bytes = json.dumps(data).encode()
            req = urllib.request.Request(url, data=json_bytes)
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=timeout) as res:
                return json.loads(res.read().decode())
