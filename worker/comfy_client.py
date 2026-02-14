"""
Compatibility wrapper — delegates to core.comfy_client.ComfyUIClient.

This file exists so that worker/agent.py can still do:
    from comfy_client import ComfyClient
while the actual implementation lives in core/comfy_client.py.
"""

import sys
import os

# Add project root to path so core/ is importable
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from core.comfy_client import ComfyUIClient


class ComfyClient:
    """
    Legacy wrapper around ComfyUIClient for backward compatibility.

    Maps the old interface to the new unified client.
    """

    def __init__(self, base_url="http://127.0.0.1:8188"):
        self._client = ComfyUIClient(base_url)
        self.base_url = base_url

    def queue_prompt(self, workflow: dict, client_id: str):
        """Submit a workflow. client_id is now managed internally."""
        self._client.client_id = client_id
        return self._client.queue_prompt(workflow)

    def get_history(self, prompt_id: str):
        return self._client.get_history(prompt_id)

    def is_reachable(self):
        return self._client.is_reachable()

    def get_images(self, filename: str, subfolder: str = "", type: str = "output"):
        return self._client.get_image_url(filename, subfolder, type)
