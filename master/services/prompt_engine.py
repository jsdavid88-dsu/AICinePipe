from typing import List, Optional
from ..models.shot import Shot
from ..models.character import Character
from ..models.cinematic import CinematicOption

class PromptEngine:
    @staticmethod
    def assemble_prompt(shot: Shot, 
                       characters: List[Character], 
                       cinematic: Optional[CinematicOption] = None) -> str:
        """
        Shot, Character, CinematicOption 정보를 기반으로 최종 프롬프트를 조립합니다.
        Airtable의 CONCATENATE 수식 로직을 기반으로 합니다.
        """
        
        parts = []
        
        # 1. 스타일 (Cinematic Option)
        if cinematic:
            style_prefix = []
            if cinematic.style:
                style_prefix.append(f"A {cinematic.style} image of")
            else:
                style_prefix.append("A cinematic shot of")
                
            parts.append(" ".join(style_prefix))
        else:
            parts.append("A cinematic shot of")
            
        # 2. 주체 및 액션 (Char + Shot Action)
        # 캐릭터 설명 조합
        char_descriptions = []
        for char in characters:
            desc = char.description
            # 캐릭터 의상이 지정된 경우 (나중에 shot.clothing_overrides 등으로 확장 가능)
            if char.default_clothing:
                desc += f" wearing {char.default_clothing}"
            char_descriptions.append(desc)
            
        if char_descriptions:
            subject_str = " and ".join(char_descriptions)
            parts.append(f"{subject_str}, {shot.action}")
        else:
            # 캐릭터가 없는 풍경 샷 등
            parts.append(f"{shot.scene_description}, {shot.action}")
            
        # 3. 환경 (Cinematic Environment)
        if cinematic and cinematic.environment:
            parts.append(f"set in {cinematic.environment}")
        elif "set in" not in shot.scene_description: # 중복 방지
             parts.append(f"set in {shot.scene_description}")

        # 4. 카메라 및 기술정 세부사항 (Camera Details)
        if cinematic:
            camera_details = []
            if cinematic.camera_body:
                camera_details.append(f"captured with {cinematic.camera_body}")
            if cinematic.focal_length:
                camera_details.append(f"{cinematic.focal_length}")
            if cinematic.lens_type:
                camera_details.append(f"{cinematic.lens_type} lens")
            if cinematic.film_stock:
                camera_details.append(f"{cinematic.film_stock} film look")
                
            if camera_details:
                parts.append(", ".join(camera_details))
                
        # 5. 조명 및 분위기 (Lighting & Atmosphere)
        if cinematic:
            mood_details = []
            if cinematic.lighting_source or cinematic.lighting_style:
                light = f"{cinematic.lighting_source or ''} {cinematic.lighting_style or ''}".strip()
                if light: mood_details.append(f"{light} lighting")
                
            if cinematic.atmosphere:
                mood_details.append(f"{cinematic.atmosphere} atmosphere")
            
            if cinematic.filter_type:
                mood_details.append(f"{cinematic.filter_type} filter")
            
            if cinematic.look_and_feel:
                mood_details.append(f"style of {cinematic.look_and_feel}")
                
            if mood_details:
                parts.append(", ".join(mood_details))

        # 6. LoRA Trigger Words (자동 추가)
        trigger_words = []
        for char in characters:
            if char.use_lora and char.trigger_words:
                trigger_words.extend(char.trigger_words)
        
        # 중복 제거 및 추가
        if trigger_words:
            unique_triggers = list(dict.fromkeys(trigger_words)) # 순서 유지 중복 제거
            parts.append(", ".join(unique_triggers))

        # 7. 포맷 (Aspect Ratio는 프롬프트 텍스트보다는 생성 설정에 가깝지만, 텍스트로도 명시 가능)
        if cinematic and cinematic.aspect_ratio:
            parts.append(f"--ar {cinematic.aspect_ratio.replace(':', ':')}")

        # 최종 조립
        final_prompt = ", ".join(parts)
        
        # 불필요한 공백 및 문장 부호 정리
        final_prompt = final_prompt.replace(" ,", ",").replace(",,", ",").strip()
        
        return final_prompt

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
