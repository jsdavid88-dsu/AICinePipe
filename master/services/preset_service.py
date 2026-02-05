import json
import os
import glob
from typing import List, Dict, Optional
from ..models.shot import TechnicalSpecs 

# Path to presets
PRESETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ref", "nano-banana-pro", "source_dump", "dist", "presets")
IMAGES_DIR_REL = "nano-banana-pro/source_dump/dist/images"

class PresetService:
    def __init__(self):
        self.presets_cache = []
        self.load_presets()

    def load_presets(self):
        """Loads all JSON presets and maps images."""
        loaded = []
        if not os.path.exists(PRESETS_DIR):
            print(f"Warning: Presets dir not found: {PRESETS_DIR}")
            return

        json_files = glob.glob(os.path.join(PRESETS_DIR, "*.json"))
        
        for fpath in json_files:
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Normalize Data
                p_data = data.get("data", {})
                
                # Image Mapping Logic
                # Camera: "s16mm film camera" -> "s16mm-film-camera.jpg"
                camera_img = self._find_image("cameras", p_data.get("camera", ""))
                lens_img = self._find_image("lenses", p_data.get("lens", ""))
                
                # Fallback to general preset layout image if available? 
                # For now just use camera as thumbnail
                
                # Check for duplicates by ID
                existing = next((x for x in loaded if x["id"] == data.get("id")), None)
                if not existing:
                    preset = {
                        "id": data.get("id"),
                        "name": data.get("name"),
                        "technical": {
                            "camera": p_data.get("camera"),
                            "film_stock": p_data.get("filmStock"),
                            "lens": p_data.get("lens"),
                            "lighting": p_data.get("lighting"),
                            "aspect_ratio": p_data.get("aspectRatio"),
                            "filter": p_data.get("filter", [])
                        },
                        "images": {
                            "camera": camera_img,
                            "lens": lens_img
                        }
                    }
                    loaded.append(preset)
            except Exception as e:
                print(f"Failed to load preset {fpath}: {e}")
                
        self.presets_cache = loaded

    def _find_image(self, category: str, name: str) -> Optional[str]:
        if not name: return None
        
        # Slugify: "Arri Alexa" -> "arri-alexa"
        slug = name.lower().replace(" ", "-")
        
        # Construct URL path (served via StaticFiles /ref)
        # Check existence? We assume structure matches.
        # Path: /ref/nano-banana-pro/source_dump/dist/images/{category}/{slug}.jpg
        
        # Local check could be done here if needed, but we'll return the URL path.
        img_url = f"/ref/{IMAGES_DIR_REL}/{category}/{slug}.jpg"
        return img_url

    def get_all(self) -> List[Dict]:
        if not self.presets_cache:
             self.load_presets()
        return self.presets_cache

    def get_by_id(self, pid: str) -> Optional[Dict]:
        for p in self.presets_cache:
            if p["id"] == pid:
                return p
        return None

# Singleton
preset_service = PresetService()
