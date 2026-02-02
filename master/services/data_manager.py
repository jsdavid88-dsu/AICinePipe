import json
import os
from typing import Dict, List, Optional
from ..models.shot import Shot
from ..models.character import Character
from ..models.cinematic import CinematicOption

class DataManager:
    def __init__(self, projects_root: str = "projects"):
        self.projects_root = projects_root
        self.current_project_id: Optional[str] = None
        self._data: Dict = {}
        
    def _get_project_path(self, project_id: str) -> str:
        return os.path.join(self.projects_root, project_id)
        
    def _get_data_file_path(self, project_id: str) -> str:
        return os.path.join(self._get_project_path(project_id), "data.json")

    def create_project(self, project_id: str) -> bool:
        path = self._get_project_path(project_id)
        if os.path.exists(path):
            return False
            
        os.makedirs(os.path.join(path, "shots"), exist_ok=True)
        os.makedirs(os.path.join(path, "renders"), exist_ok=True)
        os.makedirs(os.path.join(path, "assets"), exist_ok=True)
        
        initial_data = {
            "project_id": project_id,
            "created_at": "", # Todo: Add timestamp
            "shots": [],
            "characters": [],
            "cinematics": []
        }
        
        with open(self._get_data_file_path(project_id), 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, indent=2, ensure_ascii=False)
            
        return True

    def load_project(self, project_id: str):
        path = self._get_data_file_path(project_id)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Project {project_id} not found")
            
        with open(path, 'r', encoding='utf-8') as f:
            self._data = json.load(f)
        self.current_project_id = project_id

    def save_project(self):
        if not self.current_project_id:
            raise ValueError("No project loaded")
            
        path = self._get_data_file_path(self.current_project_id)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    # --- Shoots ---
    def get_shots(self) -> List[Shot]:
        return [Shot(**s) for s in self._data.get("shots", [])]

    def add_shot(self, shot: Shot):
        # 중복 체크 등 로직 필요
        self._data.setdefault("shots", []).append(shot.dict())
        self.save_project()
        
    def update_shot(self, shot_id: str, updates: dict):
        shots = self._data.get("shots", [])
        for i, s in enumerate(shots):
            if s["id"] == shot_id:
                shots[i].update(updates)
                self.save_project()
                return Shot(**shots[i])
        return None

    # --- Characters ---
    def get_characters(self) -> List[Character]:
        return [Character(**c) for c in self._data.get("characters", [])]

    def add_character(self, character: Character):
        self._data.setdefault("characters", []).append(character.dict())
        self.save_project()

    # --- Cinematic Options ---
    def get_cinematic_options(self) -> List[CinematicOption]:
        return [CinematicOption(**c) for c in self._data.get("cinematics", [])]

    def add_cinematic_option(self, option: CinematicOption):
        self._data.setdefault("cinematics", []).append(option.dict())
        self.save_project()
