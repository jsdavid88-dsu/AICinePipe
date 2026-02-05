import json
import os
from typing import Dict, List, Optional
from ..models.shot import Shot
from ..models.character import Character
from ..models.cinematic import CinematicOption
from .filesystem_service import FileSystemService

class DataManager:
    def __init__(self, projects_root: str = "projects"):
        self.projects_root = projects_root
        self.current_project_id: Optional[str] = None
        self._data: Dict = {}
        self.fs = FileSystemService(projects_root)
        
    def _get_project_path(self, project_id: str) -> str:
        return os.path.join(self.projects_root, project_id)
        
    def _get_data_file_path(self, project_id: str) -> str:
        return os.path.join(self._get_project_path(project_id), "data.json")

    def create_project(self, project_id: str) -> bool:
        path = self._get_project_path(project_id)
        if os.path.exists(path):
            return False
            
        # Use FileSystemService to create structure
        self.fs.ensure_project_structure(project_id)
        
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

    def get_shot(self, shot_id: str) -> Optional[Shot]:
        for s in self._data.get("shots", []):
            if s["id"] == shot_id:
                return Shot(**s)
        return None

    def add_shot(self, shot: Shot):
        # 중복 체크 등 로직 필요
        self._data.setdefault("shots", []).append(shot.dict())
        
        # Ensure FS structure
        if self.current_project_id:
             # Default sequence "SQ01" if not provided
            seq = shot.sequence_id or "SQ01" 
            self.fs.ensure_shot_structure(self.current_project_id, seq, shot.id)
            
        self.save_project()
        
    def update_shot(self, shot_id: str, updates: dict):
        shots = self._data.get("shots", [])
        for i, s in enumerate(shots):
            if s["id"] == shot_id:
                shots[i].update(updates)
                self.save_project()
                return Shot(**shots[i])
        return None

    def reorder_shots(self, shot_ids: List[str]):
        current_shots = {s["id"]: s for s in self._data.get("shots", [])}
        new_order = []
        for sid in shot_ids:
            if sid in current_shots:
                new_order.append(current_shots[sid])
        
        # 누락된 샷이 있다면 뒤에 붙임 (안전장치)
        for sid, shot in current_shots.items():
            if sid not in shot_ids:
                new_order.append(shot)
                
        self._data["shots"] = new_order
        self.save_project()
        return [Shot(**s) for s in new_order]

    # --- Characters ---
    def get_characters(self) -> List[Character]:
        return [Character(**c) for c in self._data.get("characters", [])]

    def get_character(self, character_id: str) -> Optional[Character]:
        for c in self._data.get("characters", []):
            if c["id"] == character_id:
                return Character(**c)
        return None

    def create_character(self, character: Character) -> Character:
        self._data.setdefault("characters", []).append(character.dict())
        self.save_project()
        return character

    def update_character(self, character_id: str, updates: dict) -> Optional[Character]:
        chars = self._data.get("characters", [])
        for i, c in enumerate(chars):
            if c["id"] == character_id:
                chars[i].update(updates)
                self.save_project()
                return Character(**chars[i])
        return None

    def delete_character(self, character_id: str) -> bool:
        chars = self._data.get("characters", [])
        initial_len = len(chars)
        self._data["characters"] = [c for c in chars if c["id"] != character_id]
        if len(self._data["characters"]) < initial_len:
            self.save_project()
            return True
        return False

    # --- Cinematic Options ---
    def get_cinematics(self) -> List[CinematicOption]:
        return [CinematicOption(**c) for c in self._data.get("cinematics", [])]

    def create_cinematic(self, option: CinematicOption) -> CinematicOption:
        self._data.setdefault("cinematics", []).append(option.dict())
        self.save_project()
        return option

    def update_cinematic(self, option_id: str, updates: dict) -> Optional[CinematicOption]:
        opts = self._data.get("cinematics", [])
        for i, o in enumerate(opts):
            if o["id"] == option_id:
                opts[i].update(updates)
                self.save_project()
                return CinematicOption(**opts[i])
        return None

    def delete_cinematic(self, option_id: str) -> bool:
        opts = self._data.get("cinematics", [])
        initial_len = len(opts)
        self._data["cinematics"] = [o for o in opts if o["id"] != option_id]
        if len(self._data["cinematics"]) < initial_len:
            self.save_project()
            return True
        return False
