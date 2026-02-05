from typing import List, Optional
from ..models.shot import Shot
from ..models.character import Character
from ..models.cinematic import CinematicOption

class PromptEngine:
    @staticmethod
    def assemble_prompt(shot: Shot, characters: List[Character]) -> str:
        """
        Assembles the final prompt based on Shot (V2) and Character information.
        """
        parts = []
        
        # 1. Technical / Cinematic Style (Prefix)
        tech = shot.technical
        if tech:
            # E.g. "A cinematic shot of..."
            # We can use camera/lens info here or at the end. 
            # Common pattern: "[Style] shot of [Subject]..."
            prefix = "A cinematic shot of"
            if tech.lighting:
                prefix = f"A {tech.lighting} lighting shot of"
            parts.append(prefix)
        else:
            parts.append("A cinematic shot of")

        # 2. Subjects & Action
        subject_descs = []
        
        # Map characters by ID for easy lookup if needed, but we iterate shot.subjects
        char_map = {c.id: c for c in characters}
        
        for subject in shot.subjects:
            char = char_map.get(subject.character_id)
            if char:
                # Name (Trigger Word)
                # Use name or trigger word? Usually name + description or just name if trained.
                # Let's use Name + Description for now, or just Name if known
                desc_part = char.name
                
                # Costume: Override > Default > None
                costume = subject.costume_override or char.default_clothing
                if costume:
                    desc_part += f" wearing {costume}"
                
                # Action
                if subject.action:
                    desc_part += f", {subject.action}"
                    
                subject_descs.append(desc_part)
            else:
                # Unknown character ID
                pass

        if subject_descs:
            parts.append(" and ".join(subject_descs))
        elif shot.scene_description:
            # Fallback if no subjects but description exists
            parts.append(shot.scene_description)

        # 3. Environment
        env = shot.environment
        env_parts = []
        if env.location:
            env_parts.append(f"in {env.location}")
        if env.weather:
            env_parts.append(f"during {env.weather} weather")
        if env.time_of_day:
            env_parts.append(f"at {env.time_of_day}")
            
        if env_parts:
            parts.append(", ".join(env_parts))
            
        # 4. Technical Details (Suffix)
        tech_details = []
        if tech.camera: tech_details.append(f"shot on {tech.camera}")
        if tech.film_stock: tech_details.append(f"{tech.film_stock}, film grain")
        if tech.lens: tech_details.append(f"{tech.lens} lens")
        if tech.filter: tech_details.extend(tech.filter)
        
        if tech_details:
            parts.append(", ".join(tech_details))

        # 5. LoRA Triggers (Auto-append)
        triggers = []
        for char in characters:
            if char.use_lora and char.trigger_words:
                triggers.extend(char.trigger_words)
        
        if triggers:
            parts.append(", ".join(list(set(triggers))))

        # 6. Aspect Ratio (Optional, usually handled by params but good to have in prompt for some models)
        # if tech.aspect_ratio: parts.append(f"--ar {tech.aspect_ratio}")

        # Assemble
        full_prompt = ", ".join(parts)
        return full_prompt

    @staticmethod
    def get_lora_config(characters: List[Character]) -> List[dict]:
        """
        워크플로우에 주입할 LoRA 설정 리스트를 반환합니다.
        """
        lora_configs = []
        for char in characters:
            if char.use_lora and char.lora_path:
                lora_configs.append({
                    "path": char.lora_path,
                    "strength": char.lora_strength,
                    "character_id": char.id
                })
        return lora_configs
