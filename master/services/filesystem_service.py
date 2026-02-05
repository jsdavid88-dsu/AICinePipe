import os
import json
import glob
import shutil
from typing import Optional, List, Dict
from datetime import datetime
import logging

logger = logging.getLogger("aipipeline.filesystem")


class FileSystemService:
    """
    Manages the physical file system structure following VFX production standards.
    
    프로젝트 구조 (Phase 3 로드맵 기준):
    projects/{project_id}/
    ├── project_config.json
    ├── assets/
    │   ├── characters/{CHR_name}/
    │   │   ├── lora/
    │   │   ├── reference/
    │   │   └── character_meta.json
    │   └── environments/{ENV_name}/
    ├── scenes/
    │   └── {SCN_XXX}/
    │       ├── scene_meta.json
    │       └── shots/
    │           └── {SHT_XXXX}/
    │               ├── previz/v{XXX}/
    │               ├── layout/
    │               ├── playblast/
    │               ├── render/v{XXX}/
    │               ├── comp/
    │               ├── final/
    │               └── shot_meta.json
    ├── edit/
    │   ├── proxy/
    │   ├── edl/
    │   └── timeline_state.json
    └── export/
        ├── dailies/
        └── final/
    """
    
    SHOT_TASKS = ["previz", "layout", "playblast", "render", "comp", "final"]
    ASSET_CATEGORIES = ["characters", "environments", "props", "fx"]
    
    def __init__(self, projects_root: str = "projects"):
        self.projects_root = projects_root

    def get_project_root(self, project_id: str) -> str:
        return os.path.join(self.projects_root, project_id)

    def ensure_project_structure(self, project_id: str) -> str:
        """
        Creates the complete project folder structure.
        Returns the project root path.
        """
        root = self.get_project_root(project_id)
        
        # Create all directories
        dirs = [
            "assets/characters",
            "assets/environments",
            "assets/props",
            "assets/fx",
            "scenes",
            "edit/proxy",
            "edit/edl",
            "export/dailies",
            "export/final"
        ]
        
        for d in dirs:
            os.makedirs(os.path.join(root, d), exist_ok=True)
        
        # Create project config if not exists
        config_path = os.path.join(root, "project_config.json")
        if not os.path.exists(config_path):
            config = {
                "project_id": project_id,
                "created_at": datetime.now().isoformat(),
                "version": "1.0",
                "settings": {
                    "fps": 24,
                    "resolution": [1920, 1080],
                    "aspect_ratio": "16:9"
                }
            }
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Project structure created: {root}")
        return root

    def ensure_scene_structure(self, project_id: str, scene_id: str) -> str:
        """
        Creates scene folder with metadata.
        """
        scene_path = os.path.join(
            self.get_project_root(project_id),
            "scenes",
            scene_id
        )
        
        os.makedirs(os.path.join(scene_path, "shots"), exist_ok=True)
        
        # Create scene metadata
        meta_path = os.path.join(scene_path, "scene_meta.json")
        if not os.path.exists(meta_path):
            meta = {
                "scene_id": scene_id,
                "created_at": datetime.now().isoformat(),
                "description": "",
                "shots": []
            }
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
        
        return scene_path

    def ensure_shot_structure(
        self, 
        project_id: str, 
        scene_id: str, 
        shot_id: str,
        create_meta: bool = True
    ) -> str:
        """
        Creates complete shot folder structure with all task directories.
        """
        # Ensure scene exists first
        self.ensure_scene_structure(project_id, scene_id)
        
        shot_path = os.path.join(
            self.get_project_root(project_id),
            "scenes",
            scene_id,
            "shots",
            shot_id
        )
        
        # Create task directories
        for task in self.SHOT_TASKS:
            os.makedirs(os.path.join(shot_path, task), exist_ok=True)
        
        # Create shot metadata
        if create_meta:
            meta_path = os.path.join(shot_path, "shot_meta.json")
            if not os.path.exists(meta_path):
                meta = {
                    "shot_id": shot_id,
                    "scene_id": scene_id,
                    "created_at": datetime.now().isoformat(),
                    "status": "pending",
                    "confirmed": False,
                    "locked": False,
                    "versions": {task: 0 for task in self.SHOT_TASKS},
                    "history": []
                }
                with open(meta_path, 'w', encoding='utf-8') as f:
                    json.dump(meta, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Shot structure created: {shot_path}")
        return shot_path

    def get_shot_dir(
        self, 
        project_id: str, 
        scene_id: str, 
        shot_id: str, 
        task: str = "",
        version: Optional[int] = None
    ) -> str:
        """
        Returns the directory path for a specific shot/task/version.
        """
        parts = [
            self.get_project_root(project_id),
            "scenes",
            scene_id,
            "shots",
            shot_id
        ]
        
        if task:
            parts.append(task)
            if version is not None:
                parts.append(f"v{version:03d}")
        
        return os.path.join(*parts)

    def confirm_shot(self, project_id: str, scene_id: str, shot_id: str) -> bool:
        """
        Confirms a shot, locking its structure and creating initial version folders.
        """
        shot_path = self.get_shot_dir(project_id, scene_id, shot_id)
        meta_path = os.path.join(shot_path, "shot_meta.json")
        
        if not os.path.exists(meta_path):
            logger.error(f"Shot meta not found: {meta_path}")
            return False
        
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        
        if meta.get("confirmed"):
            logger.warning(f"Shot already confirmed: {shot_id}")
            return True
        
        # Create v001 folders for key tasks
        for task in ["previz", "render"]:
            v001_path = os.path.join(shot_path, task, "v001")
            os.makedirs(v001_path, exist_ok=True)
        
        # Update metadata
        meta["confirmed"] = True
        meta["confirmed_at"] = datetime.now().isoformat()
        meta["versions"]["previz"] = 1
        meta["versions"]["render"] = 1
        meta["history"].append({
            "action": "confirmed",
            "timestamp": datetime.now().isoformat()
        })
        
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Shot confirmed: {shot_id}")
        return True

    def get_next_version(self, project_id: str, scene_id: str, shot_id: str, task: str) -> int:
        """
        Gets the next version number for a task.
        """
        task_path = self.get_shot_dir(project_id, scene_id, shot_id, task)
        
        if not os.path.exists(task_path):
            return 1
        
        # Find existing version folders
        versions = []
        for item in os.listdir(task_path):
            if item.startswith("v") and os.path.isdir(os.path.join(task_path, item)):
                try:
                    versions.append(int(item[1:]))
                except ValueError:
                    pass
        
        return max(versions, default=0) + 1

    def create_version(
        self, 
        project_id: str, 
        scene_id: str, 
        shot_id: str, 
        task: str
    ) -> str:
        """
        Creates a new version folder for a task and returns its path.
        """
        next_ver = self.get_next_version(project_id, scene_id, shot_id, task)
        version_path = self.get_shot_dir(project_id, scene_id, shot_id, task, next_ver)
        
        os.makedirs(version_path, exist_ok=True)
        
        # Update shot meta
        shot_path = self.get_shot_dir(project_id, scene_id, shot_id)
        meta_path = os.path.join(shot_path, "shot_meta.json")
        
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            
            meta["versions"][task] = next_ver
            meta["history"].append({
                "action": f"created_version",
                "task": task,
                "version": next_ver,
                "timestamp": datetime.now().isoformat()
            })
            
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created version: {shot_id}/{task}/v{next_ver:03d}")
        return version_path

    def ensure_character_structure(self, project_id: str, character_name: str) -> str:
        """
        Creates character asset folder structure.
        """
        # Sanitize name
        safe_name = "".join(c for c in character_name if c.isalnum() or c in ('_', '-', ' '))
        safe_name = safe_name.replace(' ', '_')
        folder_name = f"CHR_{safe_name}"
        
        char_path = os.path.join(
            self.get_project_root(project_id),
            "assets",
            "characters",
            folder_name
        )
        
        # Create subdirectories
        os.makedirs(os.path.join(char_path, "lora"), exist_ok=True)
        os.makedirs(os.path.join(char_path, "reference"), exist_ok=True)
        
        # Create metadata
        meta_path = os.path.join(char_path, "character_meta.json")
        if not os.path.exists(meta_path):
            meta = {
                "name": character_name,
                "folder_name": folder_name,
                "created_at": datetime.now().isoformat(),
                "lora_file": None,
                "trigger_words": [],
                "reference_images": []
            }
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
        
        return char_path

    def list_shots(self, project_id: str, scene_id: str = None) -> List[Dict]:
        """
        Lists all shots in a project or scene.
        """
        shots = []
        scenes_path = os.path.join(self.get_project_root(project_id), "scenes")
        
        if not os.path.exists(scenes_path):
            return shots
        
        scene_dirs = [scene_id] if scene_id else os.listdir(scenes_path)
        
        for scene in scene_dirs:
            shots_path = os.path.join(scenes_path, scene, "shots")
            if not os.path.exists(shots_path):
                continue
            
            for shot_dir in os.listdir(shots_path):
                meta_path = os.path.join(shots_path, shot_dir, "shot_meta.json")
                if os.path.exists(meta_path):
                    with open(meta_path, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                    shots.append(meta)
        
        return shots

