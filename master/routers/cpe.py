"""
CPE Router — Cinema Prompt Engineering API endpoints.

Endpoints for validating cin configurations, generating prompts,
listing/applying presets, and querying available options.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from ..models.cinema_enums import (
    LiveActionConfig,
    AnimationConfig,
    ProjectType,
    ValidationResult,
    VisualGrammar,
)
from ..services.rule_engine import RuleEngine
from ..utils import logger

router = APIRouter(prefix="/api/cpe", tags=["Cinema Prompt Engineering"])

# Singleton rule engine
_rule_engine = RuleEngine()


# =============================================================================
# REQUEST / RESPONSE MODELS
# =============================================================================

class ValidateRequest(BaseModel):
    """Request to validate a cinema configuration."""
    project_type: ProjectType = ProjectType.LIVE_ACTION
    live_action: Optional[LiveActionConfig] = None
    animation: Optional[AnimationConfig] = None


class GeneratePromptRequest(BaseModel):
    """Request to generate a cinematic prompt."""
    project_type: ProjectType = ProjectType.LIVE_ACTION
    live_action: Optional[LiveActionConfig] = None
    animation: Optional[AnimationConfig] = None
    scene_description: str = ""
    character_description: str = ""
    negative_prompt: str = ""
    target_model: str = "flux"  # flux, wan2.2, sdxl, ltx2


class GeneratePromptResponse(BaseModel):
    positive_prompt: str
    negative_prompt: str
    prompt_tags: list[str] = Field(default_factory=list)
    validation: Optional[ValidationResult] = None


class PresetListResponse(BaseModel):
    live_action: dict
    animation: dict


class ApplyPresetRequest(BaseModel):
    preset_id: str
    overrides: dict = Field(default_factory=dict)


class RuleCountResponse(BaseModel):
    hard: int
    warning: int
    info: int
    total: int


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/health")
async def cpe_health():
    """CPE engine health check."""
    counts = _rule_engine.get_rule_count()
    return {
        "status": "ok",
        "rule_count": counts,
        "preset_count": {
            "live_action": len(_rule_engine.list_presets()["live_action"]),
            "animation": len(_rule_engine.list_presets()["animation"]),
        }
    }


@router.post("/validate", response_model=ValidationResult)
async def validate_config(request: ValidateRequest):
    """Validate a cinema configuration against all rules."""
    if request.project_type == ProjectType.LIVE_ACTION:
        config = request.live_action or LiveActionConfig()
        result = _rule_engine.validate_live_action(config)
    else:
        config = request.animation or AnimationConfig()
        result = _rule_engine.validate_animation(config)

    return result


@router.post("/generate-prompt", response_model=GeneratePromptResponse)
async def generate_prompt(request: GeneratePromptRequest):
    """Generate a cinematic prompt based on configuration."""

    tags = []
    negative_tags = []

    if request.project_type == ProjectType.LIVE_ACTION:
        config = request.live_action or LiveActionConfig()

        # Validate first
        validation = _rule_engine.validate_live_action(config)

        # Build prompt tags from configuration
        # Camera & Lens
        camera_name = config.camera.body.value.replace("_", " ")
        tags.append(f"shot on {camera_name}")

        lens_name = config.lens.family.value.replace("_", " ")
        tags.append(f"{lens_name} {config.lens.focal_length_mm}mm")

        if config.lens.is_anamorphic:
            tags.append("anamorphic lens")
            tags.append("lens flare")

        # Film stock
        if config.camera.film_stock.value != "None":
            stock_name = config.camera.film_stock.value.replace("_", " ")
            tags.append(f"shot on {stock_name}")
            tags.append("film grain")

        # Aspect ratio
        tags.append(f"{config.camera.aspect_ratio.value} aspect ratio")

        # Lighting
        time_name = config.lighting.time_of_day.value.replace("_", " ").lower()
        tags.append(f"{time_name} lighting")

        source_name = config.lighting.source.value.replace("_", " ").lower()
        tags.append(f"{source_name}")

        style_name = config.lighting.style.value.replace("_", " ").lower()
        tags.append(f"{style_name} lighting")

        # Visual Grammar
        mood_name = config.visual_grammar.mood.value.replace("_", " ").lower()
        tags.append(f"{mood_name} mood")

        shot_name = config.visual_grammar.shot_size.value
        shot_map = {
            "EWS": "extreme wide shot",
            "WS": "wide shot",
            "MWS": "medium wide shot",
            "MS": "medium shot",
            "MCU": "medium close up",
            "CU": "close up",
            "BCU": "big close up",
            "ECU": "extreme close up",
            "OTS": "over the shoulder",
            "POV": "point of view",
        }
        tags.append(shot_map.get(shot_name, shot_name.lower()))

        comp_name = config.visual_grammar.composition.value.replace("_", " ").lower()
        tags.append(comp_name)

        # Color tone
        color_name = config.visual_grammar.color_tone.value.replace("_", " ").lower()
        tags.append(f"{color_name} color grading")

        # Movement
        if config.movement.movement_type.value != "Static":
            move_name = config.movement.movement_type.value.replace("_", " ").lower()
            tags.append(f"camera {move_name}")

            equip_name = config.movement.equipment.value.replace("_", " ").lower()
            tags.append(f"{equip_name}")

        # Quality tags
        tags.extend(["cinematic", "professional cinematography", "8k", "high detail"])

        # Build negative prompt
        negative_tags = ["amateur", "low quality", "blurry", "overexposed", "underexposed"]

    else:
        config = request.animation or AnimationConfig()
        validation = _rule_engine.validate_animation(config)

        # Animation prompt building
        medium_name = config.medium.value
        tags.append(f"{medium_name} animation")

        domain_name = config.style_domain.value.replace("_", " ")
        tags.append(f"{domain_name} style")

        # Rendering
        line_name = config.rendering.line_treatment.value.lower()
        if line_name != "none":
            tags.append(f"{line_name} linework")

        color_app = config.rendering.color_application.value.replace("_", " ").lower()
        tags.append(f"{color_app} coloring")

        light_model = config.rendering.lighting_model.value.replace("_", " ").lower()
        tags.append(f"{light_model} lighting")

        surface = config.rendering.surface_detail.value.lower()
        tags.append(f"{surface} surface detail")

        # Visual grammar
        mood_name = config.visual_grammar.mood.value.replace("_", " ").lower()
        tags.append(f"{mood_name} mood")

        tags.extend(["high quality", "masterpiece"])
        negative_tags = ["low quality", "amateur", "blurry"]

    # Combine
    prompt_parts = []
    if request.scene_description:
        prompt_parts.append(request.scene_description)
    if request.character_description:
        prompt_parts.append(request.character_description)
    prompt_parts.extend(tags)

    positive = ", ".join(prompt_parts)
    negative = ", ".join(negative_tags)
    if request.negative_prompt:
        negative = f"{request.negative_prompt}, {negative}"

    return GeneratePromptResponse(
        positive_prompt=positive,
        negative_prompt=negative,
        prompt_tags=tags,
        validation=validation,
    )


@router.get("/presets", response_model=PresetListResponse)
async def list_presets():
    """List all available cinema presets."""
    return _rule_engine.list_presets()


@router.get("/presets/{preset_id}")
async def get_preset(preset_id: str):
    """Get a specific preset by ID."""
    preset = _rule_engine.get_preset(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found")
    return preset


@router.post("/apply-preset")
async def apply_preset(request: ApplyPresetRequest):
    """Apply a preset and return the configured result with validation."""
    preset = _rule_engine.get_preset(request.preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail=f"Preset '{request.preset_id}' not found")

    # Merge overrides
    merged = {**preset, **request.overrides}

    return {
        "preset_id": request.preset_id,
        "config": merged,
        "message": f"Preset '{preset['name']}' applied successfully",
    }


@router.get("/rules/count", response_model=RuleCountResponse)
async def get_rule_count():
    """Get the count of validation rules by severity."""
    return _rule_engine.get_rule_count()


@router.get("/enums/{enum_name}")
async def get_enum_values(enum_name: str):
    """Get all values for a specific enum."""
    from ..models import cinema_enums

    # Map of available enums
    enum_map = {
        "shot_size": cinema_enums.ShotSize,
        "composition": cinema_enums.Composition,
        "mood": cinema_enums.Mood,
        "color_tone": cinema_enums.ColorTone,
        "camera_body": cinema_enums.CameraBody,
        "camera_type": cinema_enums.CameraType,
        "camera_manufacturer": cinema_enums.CameraManufacturer,
        "sensor_size": cinema_enums.SensorSize,
        "weight_class": cinema_enums.WeightClass,
        "lens_family": cinema_enums.LensFamily,
        "lens_manufacturer": cinema_enums.LensManufacturer,
        "lens_mount": cinema_enums.LensMountType,
        "film_stock": cinema_enums.FilmStock,
        "aspect_ratio": cinema_enums.AspectRatio,
        "movement_equipment": cinema_enums.MovementEquipment,
        "movement_type": cinema_enums.MovementType,
        "movement_timing": cinema_enums.MovementTiming,
        "time_of_day": cinema_enums.TimeOfDay,
        "lighting_source": cinema_enums.LightingSource,
        "lighting_style": cinema_enums.LightingStyle,
        "animation_medium": cinema_enums.AnimationMedium,
        "style_domain": cinema_enums.StyleDomain,
        "line_treatment": cinema_enums.LineTreatment,
        "color_application": cinema_enums.ColorApplication,
        "surface_detail": cinema_enums.SurfaceDetail,
        "motion_style": cinema_enums.MotionStyle,
        "virtual_camera": cinema_enums.VirtualCamera,
    }

    if enum_name not in enum_map:
        raise HTTPException(
            status_code=404,
            detail=f"Enum '{enum_name}' not found. Available: {list(enum_map.keys())}"
        )

    enum_class = enum_map[enum_name]
    return {
        "enum_name": enum_name,
        "values": [{"name": e.name, "value": e.value} for e in enum_class],
        "count": len(enum_class),
    }


@router.get("/enums")
async def list_enums():
    """List all available enum types."""
    return {
        "enums": [
            "shot_size", "composition", "mood", "color_tone",
            "camera_body", "camera_type", "camera_manufacturer",
            "sensor_size", "weight_class",
            "lens_family", "lens_manufacturer", "lens_mount",
            "film_stock", "aspect_ratio",
            "movement_equipment", "movement_type", "movement_timing",
            "time_of_day", "lighting_source", "lighting_style",
            "animation_medium", "style_domain",
            "line_treatment", "color_application", "surface_detail",
            "motion_style", "virtual_camera",
        ]
    }
