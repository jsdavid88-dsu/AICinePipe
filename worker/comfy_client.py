import requests
import json
import time

class ComfyClient:
    def __init__(self, base_url="http://127.0.0.1:8188"):
        self.base_url = base_url

    def queue_prompt(self, workflow: dict, client_id: str):
        p = {"prompt": workflow, "client_id": client_id}
        resp = requests.post(f"{self.base_url}/prompt", json=p)
        resp.raise_for_status()
        return resp.json()

    def get_history(self, prompt_id: str):
        resp = requests.get(f"{self.base_url}/history/{prompt_id}")
        resp.raise_for_status()
        return resp.json()

    def is_reachable(self):
        try:
            requests.get(f"{self.base_url}/system_stats", timeout=2)
            return True
        except:
            return False
            
    def get_images(self, filename: str, subfolder: str = "", type: str = "output"):
        # 이미지 다운로드 URL 반환 또는 바이너리 반환
        return f"{self.base_url}/view?filename={filename}&subfolder={subfolder}&type={type}"
