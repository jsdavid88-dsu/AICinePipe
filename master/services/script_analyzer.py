"""
Script Analyzer Service — LLM-based script → shot list generation.

Inspired by huobao-drama's storyboard_service.go, adapted for our pipeline.
Supports multiple LLM providers via llm_provider abstraction:
  - OpenAI (GPT-4o, GPT-4)
  - Anthropic (Claude 3.5/4)
  - Google Gemini (Gemini 2.0)
  - OpenAI-compatible (Ollama, vLLM, LiteLLM)
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from loguru import logger

from .llm_provider import LLMConfig, LLMProvider, create_llm_provider


# ── Result Model ────────────────────────────────────────────────────────────

@dataclass
class GeneratedShot:
    """A single shot generated from script analysis."""
    shot_number: int = 0
    title: str = ""
    shot_type: str = ""          # wide, full, medium, close-up, extreme close-up
    angle: str = ""              # eye-level, low, high, dutch, bird's eye
    movement: str = ""           # static, pan, tilt, dolly, tracking, crane
    action: str = ""             # Character actions
    dialogue: str = ""           # Character dialogue
    scene_description: str = ""  # Full scene description for the shot
    location: str = ""           # Scene location
    time_of_day: str = ""        # Time of day / lighting
    atmosphere: str = ""         # Mood / atmosphere
    emotion: str = ""            # Emotional beat
    duration: float = 4.0        # Estimated duration (seconds)
    image_prompt: str = ""       # Prompt for image generation
    video_prompt: str = ""       # Prompt for video generation
    characters: List[str] = field(default_factory=list)
    is_primary: bool = True      # Primary shot vs linking shot


# ── Prompt Templates ────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a professional cinematographer and storyboard artist.
Your task is to analyze a script or story description and break it down into 
individual camera shots for an AI-powered animation pipeline.

Each shot should be a single camera setup capturing one key moment or action.
Think like a film director: consider shot composition, camera movement, 
character blocking, lighting, and emotional beats.

Output MUST be valid JSON."""

USER_PROMPT_TEMPLATE = """Analyze the following script/description and generate a detailed shot list.

## Script Content
{script_text}

{character_context}

## Requirements
- Break down every scene into individual shots (one action per shot)
- Every line of dialogue should have a corresponding shot
- Each shot duration should be 4-12 seconds
- Use cinematic terminology for shot types and camera movements
- Generate image_prompt and video_prompt for each shot
- image_prompt: Static first-frame description for image generation
- video_prompt: Dynamic description including movement and action

## Shot Types
- wide / establishing: Full scene context
- full: Character head to toe
- medium: Waist up
- close-up: Face/details
- extreme close-up: Eyes, hands, objects

## Camera Angles
- eye-level, low-angle, high-angle, dutch, bird's-eye, worm's-eye

## Camera Movements
- static, pan-left, pan-right, tilt-up, tilt-down, dolly-in, dolly-out
- tracking, crane-up, crane-down, orbital, handheld

## Output Format
Return a JSON object:
{{
  "shots": [
    {{
      "shot_number": 1,
      "title": "Brief 3-5 word title",
      "shot_type": "medium",
      "angle": "eye-level",
      "movement": "static",
      "action": "Detailed action description (25+ chars)",
      "dialogue": "Character: \\"Line\\"  or empty string",
      "scene_description": "Full scene description for pipeline",
      "location": "Detailed location (20+ chars)",
      "time_of_day": "Lighting and time details (15+ chars)",
      "atmosphere": "Mood, color, sound (20+ chars)",
      "emotion": "Emotional beat and intensity",
      "duration": 6,
      "image_prompt": "Static scene description for image AI",
      "video_prompt": "Dynamic scene with movement for video AI",
      "characters": ["character_name"],
      "is_primary": true
    }}
  ]
}}

Generate ALL shots needed to cover the entire script. Do not skip or summarize any content."""


# ── Script Analyzer Service ─────────────────────────────────────────────────

class ScriptAnalyzer:
    """
    LLM-powered script analysis for automatic shot list generation.
    
    Supports multiple LLM providers through the llm_provider abstraction.
    
    Workflow:
    1. Send script text to LLM with detailed storyboard prompt
    2. Parse structured JSON response
    3. Return list of GeneratedShot objects ready for pipeline import
    """

    def __init__(self,
                 provider: str = "openai",
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 model: str = "gpt-4o",
                 max_tokens: int = 16000,
                 temperature: float = 0.7,
                 llm_provider: Optional[LLMProvider] = None):
        """
        Initialize ScriptAnalyzer.
        
        Args:
            provider: LLM provider name ("openai", "anthropic", "gemini", "ollama")
            api_key: API key for the provider
            base_url: Custom API endpoint (for OpenAI-compatible APIs)
            model: Model name to use
            max_tokens: Maximum output tokens
            temperature: Sampling temperature
            llm_provider: Pre-configured LLMProvider (overrides other args)
        """
        if llm_provider:
            self._provider = llm_provider
        else:
            config = LLMConfig(
                provider=provider,
                api_key=api_key,
                base_url=base_url,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            self._provider = create_llm_provider(config)

    @property
    def is_available(self) -> bool:
        """Check if LLM provider is configured and available."""
        return self._provider.is_available

    # ── Public API ──────────────────────────────────────────────────────────

    def analyze_script(self,
                       script_text: str,
                       characters: Optional[List[Dict[str, str]]] = None,
                       language: str = "en") -> List[GeneratedShot]:
        """
        Analyze a script and generate a shot list.
        
        Args:
            script_text: The script or story description text
            characters: Optional list of character info dicts
            language: Output language hint
            
        Returns:
            List of GeneratedShot objects
        """
        if not self.is_available:
            raise RuntimeError(
                "LLM client not configured. Set api_key to enable script analysis."
            )

        if not script_text.strip():
            raise ValueError("Script text cannot be empty")

        logger.info(f"Analyzing script: {len(script_text)} chars, model={self.model}")

        # Build character context
        char_context = ""
        if characters:
            char_lines = []
            for c in characters:
                name = c.get("name", "Unknown")
                desc = c.get("description", "")
                char_lines.append(f"- **{name}**: {desc}")
            char_context = "## Characters\n" + "\n".join(char_lines) + "\n"

        # Build prompt
        prompt = USER_PROMPT_TEMPLATE.format(
            script_text=script_text,
            character_context=char_context,
        )

        # Call LLM
        raw_response = self._call_llm(prompt)

        # Parse response
        shots = self._parse_response(raw_response)

        logger.info(f"Generated {len(shots)} shots, "
                    f"total duration: {sum(s.duration for s in shots):.0f}s")

        return shots

    def generate_shot_dicts(self,
                            script_text: str,
                            characters: Optional[List[Dict[str, str]]] = None,
                            project_characters: Optional[List[Dict]] = None
                            ) -> List[Dict[str, Any]]:
        """
        Analyze script and return shot data ready for pipeline import.
        
        Returns list of dicts compatible with Shot model creation.
        """
        shots = self.analyze_script(script_text, characters)
        
        result = []
        for shot in shots:
            shot_dict = {
                "scene_description": shot.scene_description or shot.action,
                "dialogue": shot.dialogue or None,
                "action": shot.action or None,
                "duration_seconds": shot.duration,
                "fps": 24.0,
                "frame_count": int(shot.duration * 24),
                "generated_prompt": shot.image_prompt or None,
                "negative_prompt": None,
                "workflow_type": "text_to_image",
                "status": "pending",
            }

            # Map environment
            shot_dict["environment"] = {
                "location": shot.location,
                "weather": None,
                "time_of_day": shot.time_of_day or None,
            }

            # Map technical specs from shot analysis
            shot_dict["technical"] = {
                "camera": "Arri Alexa",
                "film_stock": "Kodak Vision3",
                "lens": "Anamorphic",
                "aspect_ratio": "16:9",
                "lighting": shot.atmosphere or None,
            }

            # Map characters by name matching
            if project_characters and shot.characters:
                subjects = []
                for char_name in shot.characters:
                    # Find matching character
                    for pc in project_characters:
                        if pc.get("name", "").lower() == char_name.lower():
                            subjects.append({
                                "character_id": pc.get("id", char_name),
                                "action": shot.action or "",
                            })
                            break
                shot_dict["subjects"] = subjects

            result.append(shot_dict)

        return result

    # ── Private: LLM Call ───────────────────────────────────────────────────

    def _call_llm(self, prompt: str) -> str:
        """Call the LLM provider and return raw text response."""
        try:
            response = self._provider.generate(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=prompt,
                json_mode=True,
            )
            logger.debug(f"LLM response ({response.provider}): {len(response.content)} chars")
            return response.content
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise RuntimeError(f"LLM API call failed: {e}") from e

    # ── Private: Response Parsing ───────────────────────────────────────────

    def _parse_response(self, raw: str) -> List[GeneratedShot]:
        """Parse LLM JSON response into GeneratedShot objects."""
        # Clean up response — remove markdown code fences if present
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            # Remove ```json ... ``` wrapper
            cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned)
            cleaned = re.sub(r"\n?```\s*$", "", cleaned)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Raw response: {raw[:500]}")
            raise RuntimeError(f"LLM returned invalid JSON: {e}") from e

        # Handle both formats: {"shots": [...]} and [...]
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("shots", data.get("storyboards", []))
        else:
            raise RuntimeError(f"Unexpected LLM response type: {type(data)}")

        shots = []
        for i, item in enumerate(items):
            shot = GeneratedShot(
                shot_number=item.get("shot_number", i + 1),
                title=item.get("title", f"Shot {i + 1}"),
                shot_type=item.get("shot_type", "medium"),
                angle=item.get("angle", "eye-level"),
                movement=item.get("movement", "static"),
                action=item.get("action", ""),
                dialogue=item.get("dialogue", ""),
                scene_description=item.get("scene_description", ""),
                location=item.get("location", ""),
                time_of_day=item.get("time_of_day", item.get("time", "")),
                atmosphere=item.get("atmosphere", ""),
                emotion=item.get("emotion", ""),
                duration=self._clamp_duration(item.get("duration", 4)),
                image_prompt=item.get("image_prompt", ""),
                video_prompt=item.get("video_prompt", ""),
                characters=item.get("characters", []),
                is_primary=item.get("is_primary", True),
            )
            shots.append(shot)

        return shots

    @staticmethod
    def _clamp_duration(d: float) -> float:
        """Clamp duration to 4-12 second range."""
        try:
            d = float(d)
        except (TypeError, ValueError):
            d = 4.0
        return max(4.0, min(12.0, d))
