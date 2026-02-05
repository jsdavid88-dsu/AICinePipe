"""
Naming Convention Engine for AIPipeline.

Generates standardized names and paths following VFX production conventions.
"""

import os
import re
from typing import Optional
from datetime import datetime


class NamingConvention:
    """
    VFX 프로덕션 표준 네이밍 컨벤션 엔진.
    
    프로젝트 구조:
    {project}/
    ├── assets/
    │   ├── characters/{CHR_name}/
    │   └── environments/{ENV_name}/
    ├── scenes/
    │   └── {SCN_XXX}/
    │       └── shots/
    │           └── {SHT_XXXX}/
    │               ├── previz/v{XXX}/
    │               ├── layout/v{XXX}/
    │               ├── render/v{XXX}/
    │               ├── comp/v{XXX}/
    │               └── final/v{XXX}/
    ├── edit/
    │   ├── proxy/
    │   └── edl/
    └── export/
        ├── dailies/
        └── final/
    """
    
    # Task types available for shots
    SHOT_TASKS = ["previz", "layout", "playblast", "render", "comp", "final"]
    
    # Asset categories
    ASSET_CATEGORIES = ["characters", "environments", "props", "fx"]
    
    @staticmethod
    def sanitize_name(name: str) -> str:
        """Convert name to filesystem-safe format."""
        # Replace spaces with underscores, remove special chars
        safe = re.sub(r'[^\w\-]', '_', name)
        # Remove consecutive underscores
        safe = re.sub(r'_+', '_', safe)
        # Remove leading/trailing underscores
        return safe.strip('_')
    
    @staticmethod
    def format_version(version: int) -> str:
        """Format version number as v001, v002, etc."""
        return f"v{version:03d}"
    
    @staticmethod
    def get_project_structure(project_id: str) -> dict:
        """
        Returns the full project directory structure as a dict.
        Can be used to create all directories at once.
        """
        return {
            "root": project_id,
            "dirs": [
                "assets/characters",
                "assets/environments",
                "assets/props",
                "assets/fx",
                "scenes",
                "edit/proxy",
                "edit/edl",
                "edit/timeline",
                "export/dailies",
                "export/final",
                "config"
            ]
        }
    
    @staticmethod
    def get_shot_path(
        project_id: str,
        scene_id: str,
        shot_id: str,
        task: str = "",
        version: Optional[int] = None
    ) -> str:
        """
        Construct shot directory path.
        
        Examples:
        - get_shot_path("MyProject", "SCN-001", "SHT-0001")
          -> "MyProject/scenes/SCN-001/shots/SHT-0001"
        - get_shot_path("MyProject", "SCN-001", "SHT-0001", "previz", 1)
          -> "MyProject/scenes/SCN-001/shots/SHT-0001/previz/v001"
        """
        parts = [project_id, "scenes", scene_id, "shots", shot_id]
        
        if task:
            parts.append(task)
            if version is not None:
                parts.append(NamingConvention.format_version(version))
        
        return os.path.join(*parts)
    
    @staticmethod
    def get_asset_path(
        project_id: str,
        category: str,
        asset_name: str,
        subfolder: str = ""
    ) -> str:
        """
        Construct asset directory path.
        
        Examples:
        - get_asset_path("MyProject", "characters", "리나")
          -> "MyProject/assets/characters/CHR_리나"
        """
        safe_name = NamingConvention.sanitize_name(asset_name)
        
        # Add prefix based on category
        prefix_map = {
            "characters": "CHR",
            "environments": "ENV",
            "props": "PRP",
            "fx": "FX"
        }
        prefix = prefix_map.get(category, "")
        folder_name = f"{prefix}_{safe_name}" if prefix else safe_name
        
        parts = [project_id, "assets", category, folder_name]
        if subfolder:
            parts.append(subfolder)
        
        return os.path.join(*parts)
    
    @staticmethod
    def get_filename(
        shot_id: str,
        task: str,
        version: int,
        extension: str = "png",
        suffix: str = ""
    ) -> str:
        """
        Generate standardized filename.
        
        Example:
        - get_filename("SHT-0001", "previz", 1, "png")
          -> "SHT-0001_previz_v001.png"
        """
        parts = [shot_id, task, NamingConvention.format_version(version)]
        if suffix:
            parts.append(suffix)
        
        filename = "_".join(parts)
        return f"{filename}.{extension}"
    
    @staticmethod
    def parse_shot_id(shot_id: str) -> dict:
        """
        Parse shot ID to extract components.
        
        Example:
        - parse_shot_id("SHT-20260204-0001")
          -> {"prefix": "SHT", "date": "20260204", "number": 1}
        """
        parts = shot_id.split("-")
        if len(parts) >= 3:
            return {
                "prefix": parts[0],
                "date": parts[1],
                "number": int(parts[2])
            }
        elif len(parts) == 2:
            return {
                "prefix": parts[0],
                "number": int(parts[1])
            }
        return {"raw": shot_id}


# Export singleton-style
naming = NamingConvention()
