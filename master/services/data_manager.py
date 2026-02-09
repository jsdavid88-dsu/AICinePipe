"""
Data manager for AIPipeline.

Provides CRUD operations backed by SQLite, with backward-compatible
JSON import on first run.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

from loguru import logger

from ..db.database import get_database
from ..models.shot import Shot
from ..models.character import Character
from ..models.cinematic import CinematicOption
from .filesystem_service import FileSystemService


class DataManager:
    def __init__(self, projects_root: str = "projects"):
        self.projects_root = projects_root
        self.current_project_id: Optional[str] = None
        self._data: Dict = {}  # kept for backward compat during transition
        self.fs = FileSystemService(projects_root)
        self.db = get_database()

    # -- Project Management --

    def _get_project_path(self, project_id: str) -> str:
        return os.path.join(self.projects_root, project_id)

    def _get_data_file_path(self, project_id: str) -> str:
        return os.path.join(self._get_project_path(project_id), "data.json")

    def create_project(self, project_id: str) -> bool:
        path = self._get_project_path(project_id)
        if os.path.exists(path):
            return False

        # Filesystem structure
        self.fs.ensure_project_structure(project_id)

        now = datetime.now().isoformat()
        self.db.execute(
            "INSERT OR IGNORE INTO projects (id, description, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (project_id, "", now, now),
        )

        # Also write legacy data.json for backward compat
        initial_data = {
            "project_id": project_id,
            "created_at": now,
            "shots": [],
            "characters": [],
            "cinematics": [],
        }
        data_path = self._get_data_file_path(project_id)
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(initial_data, f, indent=2, ensure_ascii=False)

        return True

    def load_project(self, project_id: str):
        path = self._get_project_path(project_id)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Project {project_id} not found")

        # Ensure project exists in DB (import from JSON if needed)
        existing = self.db.fetchone("SELECT id FROM projects WHERE id = ?", (project_id,))
        if not existing:
            self._import_project_from_json(project_id)

        self.current_project_id = project_id

        # Keep _data in sync for any code that still accesses it directly
        self._data = {
            "project_id": project_id,
            "shots": [s.dict() for s in self.get_shots()],
            "characters": [c.dict() for c in self.get_characters()],
            "cinematics": [c.dict() for c in self.get_cinematics()],
        }

    def save_project(self):
        """Update project timestamp. Legacy JSON sync."""
        if not self.current_project_id:
            raise ValueError("No project loaded")

        now = datetime.now().isoformat()
        self.db.execute(
            "UPDATE projects SET updated_at = ? WHERE id = ?",
            (now, self.current_project_id),
        )

    def _import_project_from_json(self, project_id: str):
        """One-time import of existing JSON project data into SQLite."""
        data_path = self._get_data_file_path(project_id)
        if not os.path.exists(data_path):
            # No JSON data to import; just create the DB record
            now = datetime.now().isoformat()
            self.db.execute(
                "INSERT OR IGNORE INTO projects (id, description, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (project_id, "", now, now),
            )
            return

        logger.info(f"Importing project '{project_id}' from JSON to SQLite")
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        now = datetime.now().isoformat()
        self.db.execute(
            "INSERT OR IGNORE INTO projects (id, description, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (project_id, data.get("description", ""), data.get("created_at", now), now),
        )

        # Import shots
        for s in data.get("shots", []):
            self._upsert_shot_row(project_id, s)

        # Import characters
        for c in data.get("characters", []):
            self._upsert_character_row(project_id, c)

        # Import cinematics
        for c in data.get("cinematics", []):
            self._upsert_cinematic_row(project_id, c)

        logger.info(f"Imported project '{project_id}': {len(data.get('shots', []))} shots, "
                     f"{len(data.get('characters', []))} characters, "
                     f"{len(data.get('cinematics', []))} cinematics")

    # -- Shots --

    def get_shots(self) -> List[Shot]:
        if not self.current_project_id:
            return []
        rows = self.db.fetchall(
            "SELECT * FROM shots WHERE project_id = ? ORDER BY rowid",
            (self.current_project_id,),
        )
        return [self._row_to_shot(r) for r in rows]

    def get_shot(self, shot_id: str) -> Optional[Shot]:
        row = self.db.fetchone("SELECT * FROM shots WHERE id = ?", (shot_id,))
        return self._row_to_shot(row) if row else None

    def add_shot(self, shot: Shot):
        if not self.current_project_id:
            raise ValueError("No project loaded")

        self._upsert_shot_row(self.current_project_id, shot.dict())

        # Ensure FS structure
        seq = shot.sequence_id or "SQ01"
        self.fs.ensure_shot_structure(self.current_project_id, seq, shot.id)

    def update_shot(self, shot_id: str, updates: dict) -> Optional[Shot]:
        existing = self.db.fetchone("SELECT * FROM shots WHERE id = ?", (shot_id,))
        if not existing:
            return None

        # Merge updates
        shot_dict = dict(existing)
        for key, value in updates.items():
            if key in shot_dict:
                shot_dict[key] = value

        shot_dict["updated_at"] = datetime.now().isoformat()
        project_id = shot_dict.get("project_id", self.current_project_id)
        self._upsert_shot_row(project_id, shot_dict)

        return self.get_shot(shot_id)

    def reorder_shots(self, shot_ids: List[str]) -> List[Shot]:
        # SQLite rowid-based ordering: delete and re-insert in order
        if not self.current_project_id:
            return []

        all_shots = self.db.fetchall(
            "SELECT * FROM shots WHERE project_id = ?",
            (self.current_project_id,),
        )
        shot_map = {s["id"]: s for s in all_shots}

        # Build ordered list
        ordered = []
        for sid in shot_ids:
            if sid in shot_map:
                ordered.append(shot_map.pop(sid))
        # Append any remaining shots not in the reorder list
        for s in shot_map.values():
            ordered.append(s)

        # Delete and re-insert in order
        self.db.execute(
            "DELETE FROM shots WHERE project_id = ?",
            (self.current_project_id,),
        )
        for s in ordered:
            self._upsert_shot_row(self.current_project_id, s)

        return self.get_shots()

    # -- Characters --

    def get_characters(self) -> List[Character]:
        if not self.current_project_id:
            return []
        rows = self.db.fetchall(
            "SELECT * FROM characters WHERE project_id = ? ORDER BY rowid",
            (self.current_project_id,),
        )
        return [self._row_to_character(r) for r in rows]

    def get_character(self, character_id: str) -> Optional[Character]:
        row = self.db.fetchone("SELECT * FROM characters WHERE id = ?", (character_id,))
        return self._row_to_character(row) if row else None

    def create_character(self, character: Character) -> Character:
        if not self.current_project_id:
            raise ValueError("No project loaded")
        self._upsert_character_row(self.current_project_id, character.dict())
        return character

    def update_character(self, character_id: str, updates: dict) -> Optional[Character]:
        existing = self.db.fetchone("SELECT * FROM characters WHERE id = ?", (character_id,))
        if not existing:
            return None

        char_dict = dict(existing)
        for key, value in updates.items():
            if key in char_dict:
                char_dict[key] = value
        char_dict["updated_at"] = datetime.now().isoformat()
        project_id = char_dict.get("project_id", self.current_project_id)
        self._upsert_character_row(project_id, char_dict)

        return self.get_character(character_id)

    def delete_character(self, character_id: str) -> bool:
        existing = self.db.fetchone("SELECT id FROM characters WHERE id = ?", (character_id,))
        if not existing:
            return False
        self.db.execute("DELETE FROM characters WHERE id = ?", (character_id,))
        return True

    # -- Cinematics --

    def get_cinematics(self) -> List[CinematicOption]:
        if not self.current_project_id:
            return []
        rows = self.db.fetchall(
            "SELECT * FROM cinematics WHERE project_id = ? ORDER BY rowid",
            (self.current_project_id,),
        )
        return [self._row_to_cinematic(r) for r in rows]

    def create_cinematic(self, option: CinematicOption) -> CinematicOption:
        if not self.current_project_id:
            raise ValueError("No project loaded")
        self._upsert_cinematic_row(self.current_project_id, option.dict())
        return option

    def update_cinematic(self, option_id: str, updates: dict) -> Optional[CinematicOption]:
        existing = self.db.fetchone("SELECT * FROM cinematics WHERE id = ?", (option_id,))
        if not existing:
            return None

        cin_dict = dict(existing)
        for key, value in updates.items():
            if key in cin_dict:
                cin_dict[key] = value
        cin_dict["updated_at"] = datetime.now().isoformat()
        project_id = cin_dict.get("project_id", self.current_project_id)
        self._upsert_cinematic_row(project_id, cin_dict)

        return self.get_cinematic(option_id)

    def get_cinematic(self, option_id: str) -> Optional[CinematicOption]:
        row = self.db.fetchone("SELECT * FROM cinematics WHERE id = ?", (option_id,))
        return self._row_to_cinematic(row) if row else None

    def delete_cinematic(self, option_id: str) -> bool:
        existing = self.db.fetchone("SELECT id FROM cinematics WHERE id = ?", (option_id,))
        if not existing:
            return False
        self.db.execute("DELETE FROM cinematics WHERE id = ?", (option_id,))
        return True

    # -- Row Conversion Helpers --

    def _upsert_shot_row(self, project_id: str, data: dict) -> None:
        """Insert or replace a shot row from a dict (model or raw)."""
        subjects = data.get("subjects", [])
        if isinstance(subjects, list):
            subjects = json.dumps(subjects, ensure_ascii=False)

        env = data.get("environment", {})
        if isinstance(env, dict):
            env = json.dumps(env, ensure_ascii=False)

        tech = data.get("technical", {})
        if isinstance(tech, dict):
            tech = json.dumps(tech, ensure_ascii=False)

        char_ids = data.get("character_ids", [])
        if isinstance(char_ids, list):
            char_ids = json.dumps(char_ids, ensure_ascii=False)

        ref_imgs = data.get("reference_images", [])
        if isinstance(ref_imgs, list):
            ref_imgs = json.dumps(ref_imgs, ensure_ascii=False)

        self.db.execute(
            """INSERT OR REPLACE INTO shots (
                id, project_id, sequence_id, scene_description, dialogue,
                subjects, environment, technical,
                action, character_ids, cinematic_id,
                generated_prompt, negative_prompt, seed,
                reference_images, generated_image_path, generated_video_path,
                frame_count, fps, duration_seconds, timecode_in, timecode_out,
                status, workflow_type, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                data.get("id"),
                project_id,
                data.get("sequence_id"),
                data.get("scene_description", ""),
                data.get("dialogue"),
                subjects,
                env,
                tech,
                data.get("action"),
                char_ids,
                data.get("cinematic_id"),
                data.get("generated_prompt"),
                data.get("negative_prompt"),
                data.get("seed"),
                ref_imgs,
                data.get("generated_image_path"),
                data.get("generated_video_path"),
                data.get("frame_count", 24),
                data.get("fps", 24.0),
                data.get("duration_seconds", 1.0),
                data.get("timecode_in"),
                data.get("timecode_out"),
                data.get("status", "pending"),
                data.get("workflow_type", "text_to_image"),
                data.get("created_at", datetime.now().isoformat()),
                data.get("updated_at", datetime.now().isoformat()),
            ),
        )

    def _upsert_character_row(self, project_id: str, data: dict) -> None:
        self.db.execute(
            """INSERT OR REPLACE INTO characters (
                id, project_id, name, description, reference_sheet,
                lora_path, lora_strength, trigger_words, use_lora,
                default_clothing, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                data.get("id"),
                project_id,
                data.get("name", ""),
                data.get("description", ""),
                data.get("reference_sheet"),
                data.get("lora_path"),
                data.get("lora_strength", 0.8),
                data.get("trigger_words", ""),
                1 if data.get("use_lora") else 0,
                data.get("default_clothing"),
                data.get("created_at", datetime.now().isoformat()),
                data.get("updated_at", datetime.now().isoformat()),
            ),
        )

    def _upsert_cinematic_row(self, project_id: str, data: dict) -> None:
        filters_val = data.get("filters", [])
        if isinstance(filters_val, list):
            filters_val = json.dumps(filters_val, ensure_ascii=False)

        raw_data = data.get("raw_data")
        if isinstance(raw_data, dict):
            raw_data = json.dumps(raw_data, ensure_ascii=False)

        self.db.execute(
            """INSERT OR REPLACE INTO cinematics (
                id, project_id, name, category,
                camera_body, focal_length, lens_type, film_stock,
                shot_type, lighting,
                style, environment, atmosphere, filters,
                raw_data, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                data.get("id"),
                project_id,
                data.get("name", ""),
                data.get("category", "General"),
                data.get("camera_body", "Arri Alexa"),
                data.get("focal_length", "35mm"),
                data.get("lens_type", "Anamorphic"),
                data.get("film_stock"),
                data.get("shot_type"),
                data.get("lighting"),
                data.get("style", "Cinematic"),
                data.get("environment", ""),
                data.get("atmosphere", ""),
                filters_val,
                raw_data,
                data.get("created_at", datetime.now().isoformat()),
                data.get("updated_at", datetime.now().isoformat()),
            ),
        )

    @staticmethod
    def _row_to_shot(row: dict) -> Shot:
        """Convert a SQLite row dict to a Shot model."""
        data = dict(row)
        # Parse JSON fields
        for field in ("subjects", "character_ids", "reference_images"):
            val = data.get(field)
            if isinstance(val, str):
                try:
                    data[field] = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    data[field] = []

        for field in ("environment", "technical"):
            val = data.get(field)
            if isinstance(val, str):
                try:
                    data[field] = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    data[field] = {}

        # Remove project_id (not in Shot model)
        data.pop("project_id", None)
        return Shot(**data)

    @staticmethod
    def _row_to_character(row: dict) -> Character:
        data = dict(row)
        data.pop("project_id", None)
        # Convert use_lora from int to bool
        data["use_lora"] = bool(data.get("use_lora", 0))
        return Character(**data)

    @staticmethod
    def _row_to_cinematic(row: dict) -> CinematicOption:
        data = dict(row)
        data.pop("project_id", None)

        # Parse JSON fields
        for field in ("filters",):
            val = data.get(field)
            if isinstance(val, str):
                try:
                    data[field] = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    data[field] = []

        raw = data.get("raw_data")
        if isinstance(raw, str):
            try:
                data["raw_data"] = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                data["raw_data"] = None

        return CinematicOption(**data)
