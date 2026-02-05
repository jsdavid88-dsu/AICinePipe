import os
import json
import uuid
from typing import List
from ..models.cinematic import CinematicOption
from ..services.data_manager import DataManager

REF_PRESETS_PATH = r"e:\Net\Antigravity_prj\3D_Comfy_RnD\AIPipeline_tool\ref\nano-banana-pro\source_dump\dist\presets"

class PresetImporter:
    def __init__(self, data_manager: DataManager):
        self.manager = data_manager

    def scan_and_import(self) -> int:
        if not os.path.exists(REF_PRESETS_PATH):
            print(f"Warning: Preset path not found: {REF_PRESETS_PATH}")
            return 0

        count = 0
        for filename in os.listdir(REF_PRESETS_PATH):
            if not filename.endswith(".json"):
                continue
            
            try:
                filepath = os.path.join(REF_PRESETS_PATH, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Check duplication by name (simple check)
                # Ideally check ID, but ID might overlap or be new
                # We use name as unique identifier for our 'presets'
                
                # Convert to CinematicOption
                # JSON Structure: { "id":..., "name":..., "data": { "camera":..., ... } }
                
                inner_data = data.get("data", {})
                
                option = CinematicOption(
                    id=f"PRESET-{data.get('id', str(uuid.uuid4()))}", # Prefix to avoid collision
                    name=data.get("name", filename),
                    category="Preset",
                    
                    camera_body=inner_data.get("camera", "Arri Alexa"),
                    focal_length=inner_data.get("focalLength", ""),
                    lens_type=inner_data.get("lens", ""),
                    film_stock=inner_data.get("filmStock", ""),
                    
                    shot_type=inner_data.get("shotType", ""),
                    lighting=inner_data.get("lighting", ""),
                    
                    filters=inner_data.get("filter", []),
                    
                    raw_data=data
                )
                
                # Save via DataManager
                # Check duplication by name to avoid spamming
                existing = [c for c in self.manager.get_cinematics() if c.name == option.name]
                if not existing:
                    self.manager.create_cinematic(option)
                    count += 1
                else:
                    # Update existing or skip? Let's skip for now to preserve user edits
                    pass
                
            except Exception as e:
                print(f"Failed to import {filename}: {e}")
        
        return count
