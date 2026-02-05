"""
ID Generation utilities for AIPipeline.

Provides server-side sequential ID generation with prefixes.
"""

import uuid
from datetime import datetime
from typing import Optional


class IDGenerator:
    """
    Generates unique IDs for entities following naming conventions.
    
    Formats:
    - Shot: SHT-YYYYMMDD-XXXX (e.g., SHT-20260204-0001)
    - Character: CHR-XXXX (e.g., CHR-0001)
    - Sequence: SEQ-XXX (e.g., SEQ-001)
    - Scene: SCN-XXX (e.g., SCN-001)
    """
    
    _counters = {
        "shot": 0,
        "character": 0,
        "sequence": 0,
        "scene": 0,
        "job": 0
    }
    
    @classmethod
    def generate_shot_id(cls, existing_ids: Optional[list] = None) -> str:
        """Generate a unique shot ID with 10-step increment. Format: SHT-XXXXX (e.g., SHT-00010)."""
        max_val = 0
        
        if existing_ids:
            # Find max numeric value from existing IDs
            for eid in existing_ids:
                if eid.startswith("SHT-"):
                    try:
                        # Handle SHT-00010 and legacy SHT-YYYYMMDD-XXXX
                        parts = eid.split("-")
                        val = int(parts[-1])
                        max_val = max(max_val, val)
                    except ValueError:
                        pass
        
        # Increment by 10 (VFX standard for allowing inserts)
        # If max_val is 0, next is 10
        # If max_val is 10, next is 20
        # If max_val is 15 (inserted shot), next is just +10? No, let's align to 10s.
        
        next_val = (max_val // 10 + 1) * 10
        
        return f"SHT-{next_val:05d}"
    
    @classmethod
    def generate_character_id(cls, existing_ids: Optional[list] = None) -> str:
        """Generate a unique character ID."""
        if existing_ids:
            max_counter = 0
            for eid in existing_ids:
                if eid.startswith("CHR-"):
                    try:
                        counter = int(eid.split("-")[-1])
                        max_counter = max(max_counter, counter)
                    except ValueError:
                        pass
            cls._counters["character"] = max_counter
        
        cls._counters["character"] += 1
        return f"CHR-{cls._counters['character']:04d}"
    
    @classmethod
    def generate_sequence_id(cls, existing_ids: Optional[list] = None) -> str:
        """Generate a unique sequence ID."""
        if existing_ids:
            max_counter = 0
            for eid in existing_ids:
                if eid.startswith("SEQ-"):
                    try:
                        counter = int(eid.split("-")[-1])
                        max_counter = max(max_counter, counter)
                    except ValueError:
                        pass
            cls._counters["sequence"] = max_counter
        
        cls._counters["sequence"] += 1
        return f"SEQ-{cls._counters['sequence']:03d}"
    
    @classmethod
    def generate_scene_id(cls, existing_ids: Optional[list] = None) -> str:
        """Generate a unique scene ID."""
        if existing_ids:
            max_counter = 0
            for eid in existing_ids:
                if eid.startswith("SCN-"):
                    try:
                        counter = int(eid.split("-")[-1])
                        max_counter = max(max_counter, counter)
                    except ValueError:
                        pass
            cls._counters["scene"] = max_counter
        
        cls._counters["scene"] += 1
        return f"SCN-{cls._counters['scene']:03d}"
    
    @classmethod
    def generate_job_id(cls) -> str:
        """Generate a unique job ID using UUID."""
        return f"JOB-{uuid.uuid4().hex[:12].upper()}"
    
    @classmethod
    def generate_uuid(cls) -> str:
        """Generate a raw UUID."""
        return str(uuid.uuid4())


# Singleton instance
id_generator = IDGenerator()
