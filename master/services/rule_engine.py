"""
CPE Rule Engine — validates cinema configurations and enforces constraints.

Adapted from DirectorsConsole's rule engine with our pipeline-specific additions:
- Batch validation for entire shot lists
- Prompt auto-correction suggestions
- VRAM requirement tagging per workflow
"""

from typing import Any, Callable, Optional

from ..models.cinema_enums import (
    AspectRatio,
    CameraBody,
    CameraConfig,
    CameraType,
    FilmStock,
    LensConfig,
    LensFamily,
    LightingConfig,
    LightingSource,
    LightingStyle,
    LiveActionConfig,
    AnimationConfig,
    Composition,
    Mood,
    MovementConfig,
    MovementEquipment,
    MovementType,
    MovementTiming,
    ShotSize,
    TimeOfDay,
    WeightClass,
    RuleSeverity,
    ValidationMessage,
    ValidationResult,
)

from ..utils import logger


# =============================================================================
# CAMERA CLASSIFICATION SETS
# =============================================================================

FILM_CAMERA_BODIES = {
    CameraBody.ARRICAM_ST, CameraBody.ARRICAM_LT, CameraBody.ARRI_535B,
    CameraBody.ARRI_35BL, CameraBody.ARRI_35_III, CameraBody.ARRIFLEX_35,
    CameraBody.ARRIFLEX_35BL, CameraBody.ARRIFLEX_435,
    CameraBody.PANAVISION_MILLENNIUM_XL2, CameraBody.PANAVISION_MILLENNIUM,
    CameraBody.PANAVISION_PLATINUM, CameraBody.PANAVISION_GOLD,
    CameraBody.PANAVISION_PANASTAR, CameraBody.PANAVISION_PANAFLEX,
    CameraBody.SUPER_PANAVISION_70, CameraBody.ULTRA_PANAVISION_70,
    CameraBody.PANAVISION_XL,
    CameraBody.MITCHELL_BNC, CameraBody.MITCHELL_BNCR, CameraBody.MITCHELL_BFC_65,
    CameraBody.IMAX_MSM_9802, CameraBody.IMAX_MKIV, CameraBody.IMAX_GT_BODY,
    CameraBody.ECLAIR_NPR, CameraBody.UFA_CUSTOM, CameraBody.PATHE_STUDIO,
}

PANAVISION_CAMERA_BODIES = {
    CameraBody.PANAVISION_MILLENNIUM_XL2, CameraBody.PANAVISION_MILLENNIUM,
    CameraBody.PANAVISION_PLATINUM, CameraBody.PANAVISION_GOLD,
    CameraBody.PANAVISION_PANASTAR, CameraBody.PANAVISION_PANAFLEX,
    CameraBody.SUPER_PANAVISION_70, CameraBody.ULTRA_PANAVISION_70,
    CameraBody.PANAVISION_XL,
}

PANAVISION_LENS_FAMILIES = {
    LensFamily.PANAVISION_PRIMO, LensFamily.PANAVISION_PRIMO_70,
    LensFamily.PANAVISION_ANAMORPHIC, LensFamily.PANAVISION_C_SERIES,
    LensFamily.PANAVISION_E_SERIES, LensFamily.PANAVISION_SPHERO,
    LensFamily.PANAVISION_ULTRA_SPEED,
}

LARGE_FORMAT_CAMERAS = {
    CameraBody.ALEXA_65, CameraBody.ALEXA_LF, CameraBody.ALEXA_MINI_LF,
    CameraBody.SUPER_PANAVISION_70, CameraBody.ULTRA_PANAVISION_70,
    CameraBody.MITCHELL_BFC_65,
    CameraBody.IMAX_MSM_9802, CameraBody.IMAX_MKIV, CameraBody.IMAX_GT_BODY,
}

IMAX_CAMERAS = {
    CameraBody.IMAX_MSM_9802, CameraBody.IMAX_MKIV, CameraBody.IMAX_GT_BODY,
}

HEAVY_CAMERAS = {
    CameraBody.ALEXA_65, CameraBody.VENICE_2, CameraBody.C700_FF,
    CameraBody.ARRICAM_ST, CameraBody.ARRI_535B,
    CameraBody.PANAVISION_PLATINUM, CameraBody.PANAVISION_GOLD,
    CameraBody.MITCHELL_BNC, CameraBody.MITCHELL_BNCR, CameraBody.MITCHELL_BFC_65,
    CameraBody.SUPER_PANAVISION_70, CameraBody.ULTRA_PANAVISION_70,
    CameraBody.IMAX_MSM_9802, CameraBody.IMAX_GT_BODY,
}

MEDIUM_CAMERAS = {
    CameraBody.ALEXA_35, CameraBody.V_RAPTOR_XL,
    CameraBody.ARRICAM_LT, CameraBody.ARRI_35BL, CameraBody.ARRI_35_III,
    CameraBody.PANAVISION_MILLENNIUM_XL2, CameraBody.PANAVISION_MILLENNIUM,
    CameraBody.PANAVISION_PANAFLEX, CameraBody.PANAVISION_PANASTAR,
    CameraBody.IMAX_MKIV,
}

LIGHT_CAMERAS = {
    CameraBody.ALEXA_MINI, CameraBody.ALEXA_MINI_LF, CameraBody.ALEXA_LF,
    CameraBody.V_RAPTOR, CameraBody.V_RAPTOR_X, CameraBody.KOMODO_X,
    CameraBody.FX6, CameraBody.FX9, CameraBody.POCKET_6K,
    CameraBody.Z9, CameraBody.S1H, CameraBody.MAVIC_3_CINE,
}

S35_ONLY_LENSES = {
    LensFamily.ARRI_ULTRA_PRIME, LensFamily.ARRI_MASTER_PRIME,
    LensFamily.ZEISS_MASTER_PRIME, LensFamily.COOKE_S4,
    LensFamily.PANAVISION_PRIMO,
}

HIGH_RES_CAMERAS = {
    CameraBody.V_RAPTOR, CameraBody.V_RAPTOR_X, CameraBody.V_RAPTOR_XL,
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_weight_class(body: CameraBody) -> WeightClass:
    """Get weight class for a camera body."""
    if body in HEAVY_CAMERAS:
        return WeightClass.HEAVY
    elif body in MEDIUM_CAMERAS:
        return WeightClass.MEDIUM
    elif body in LIGHT_CAMERAS:
        return WeightClass.LIGHT
    return WeightClass.ULTRA_LIGHT


def _is_film_camera(body: CameraBody) -> bool:
    return body in FILM_CAMERA_BODIES


def _era_before_year(era: str, year: int) -> bool:
    """Check if an era string represents a time before the given year."""
    era_lower = era.lower()
    decade_map = {
        "1890s": 1895, "1900s": 1905, "1910s": 1915, "1920s": 1925,
        "1930s": 1935, "1940s": 1945, "1950s": 1955, "1960s": 1965,
        "1970s": 1975, "1980s": 1985, "1990s": 1995, "2000s": 2005,
        "2010s": 2015, "2020s": 2025,
    }
    if era_lower in decade_map:
        return decade_map[era_lower] < year
    # Try parsing as a year
    try:
        return int(era) < year
    except (ValueError, TypeError):
        return False


# =============================================================================
# RULE CLASS
# =============================================================================

CheckFunc = Callable[[Any], bool]


class Rule:
    """A validation rule with condition check."""

    def __init__(
        self,
        rule_id: str,
        severity: RuleSeverity,
        message: str,
        check: CheckFunc,
        field_path: str | None = None,
    ):
        self.rule_id = rule_id
        self.severity = severity
        self.message = message
        self.check = check
        self.field_path = field_path

    def evaluate(self, config: Any) -> ValidationMessage | None:
        """Returns message if rule is VIOLATED."""
        try:
            if self.check(config):
                return ValidationMessage(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message=self.message,
                    field_path=self.field_path,
                )
        except Exception:
            # Don't crash on rule evaluation errors
            pass
        return None


# =============================================================================
# LIVE-ACTION RULES (30+ rules)
# =============================================================================

LIVE_ACTION_RULES: list[Rule] = [
    # --- FILM STOCK RULES ---
    Rule(
        rule_id="LA_DIGITAL_NO_FILM_STOCK",
        severity=RuleSeverity.HARD,
        message="Film stock cannot be selected with digital cameras.",
        field_path="camera.film_stock",
        check=lambda c: (
            not _is_film_camera(c.camera.body) and
            c.camera.film_stock != FilmStock.NONE
        ),
    ),
    Rule(
        rule_id="LA_FILM_REQUIRES_STOCK",
        severity=RuleSeverity.HARD,
        message="Film cameras require a film stock selection.",
        field_path="camera.film_stock",
        check=lambda c: (
            _is_film_camera(c.camera.body) and
            c.camera.film_stock == FilmStock.NONE
        ),
    ),
    Rule(
        rule_id="LA_65MM_STOCK_REQUIRES_65MM_CAMERA",
        severity=RuleSeverity.HARD,
        message="65mm/70mm film stocks require large format (65mm) cameras.",
        field_path="camera.film_stock",
        check=lambda c: (
            c.camera.film_stock in {
                FilmStock.KODAK_65MM_500T, FilmStock.KODAK_65MM_250D,
                FilmStock.KODAK_65MM_200T,
            } and c.camera.body not in LARGE_FORMAT_CAMERAS
        ),
    ),
    Rule(
        rule_id="LA_IMAX_STOCK_REQUIRES_IMAX",
        severity=RuleSeverity.HARD,
        message="IMAX film stocks require IMAX cameras.",
        field_path="camera.film_stock",
        check=lambda c: (
            c.camera.film_stock in {FilmStock.IMAX_500T, FilmStock.IMAX_250D} and
            c.camera.body not in IMAX_CAMERAS
        ),
    ),

    # --- ASPECT RATIO RULES ---
    Rule(
        rule_id="LA_ULTRA_PANAVISION_ASPECT",
        severity=RuleSeverity.HARD,
        message="Ultra Panavision 70 cameras use 2.76:1 anamorphic aspect ratio.",
        field_path="camera.aspect_ratio",
        check=lambda c: (
            c.camera.body == CameraBody.ULTRA_PANAVISION_70 and
            c.camera.aspect_ratio != AspectRatio.RATIO_2_76
        ),
    ),
    Rule(
        rule_id="LA_IMAX_1570_ASPECT",
        severity=RuleSeverity.WARNING,
        message="IMAX 15/70 cameras typically use 1.43:1 aspect ratio.",
        field_path="camera.aspect_ratio",
        check=lambda c: (
            c.camera.body in {CameraBody.IMAX_MSM_9802, CameraBody.IMAX_GT_BODY} and
            c.camera.aspect_ratio not in {AspectRatio.RATIO_1_43, AspectRatio.RATIO_1_90}
        ),
    ),
    Rule(
        rule_id="LA_276_REQUIRES_ULTRA_PV70",
        severity=RuleSeverity.HARD,
        message="2.76:1 aspect ratio requires Ultra Panavision 70 camera system.",
        field_path="camera.aspect_ratio",
        check=lambda c: (
            c.camera.aspect_ratio == AspectRatio.RATIO_2_76 and
            c.camera.body != CameraBody.ULTRA_PANAVISION_70
        ),
    ),

    # --- LENS MOUNT COMPATIBILITY ---
    Rule(
        rule_id="LA_PANAVISION_CLOSED_ECOSYSTEM",
        severity=RuleSeverity.HARD,
        message="Panavision cameras use proprietary mount. Only Panavision lenses are compatible.",
        field_path="lens.family",
        check=lambda c: (
            c.camera.body in PANAVISION_CAMERA_BODIES and
            c.lens.family not in PANAVISION_LENS_FAMILIES
        ),
    ),
    Rule(
        rule_id="LA_PANAVISION_LENS_REQUIRES_PV_CAMERA",
        severity=RuleSeverity.HARD,
        message="Panavision lenses require Panavision mount cameras.",
        field_path="lens.family",
        check=lambda c: (
            c.lens.family in PANAVISION_LENS_FAMILIES and
            c.camera.body not in PANAVISION_CAMERA_BODIES and
            c.camera.body != CameraBody.ALEXA_65
        ),
    ),
    Rule(
        rule_id="LA_ALEXA65_LENS_RESTRICT",
        severity=RuleSeverity.HARD,
        message="Alexa 65 (XPL mount, 65mm sensor) requires 65mm format lenses.",
        field_path="lens.family",
        check=lambda c: (
            c.camera.body == CameraBody.ALEXA_65 and
            c.lens.family not in {
                LensFamily.ARRI_PRIME_65, LensFamily.ARRI_PRIME_DNA,
                LensFamily.PANAVISION_PRIMO_70, LensFamily.HASSELBLAD_V,
                LensFamily.VINTAGE_SPHERICAL,
            }
        ),
    ),
    Rule(
        rule_id="LA_LF_NO_S35_LENS",
        severity=RuleSeverity.HARD,
        message="Large Format cameras require LF/FF lenses. S35-only lenses will vignette.",
        field_path="lens.family",
        check=lambda c: (
            c.camera.body in {CameraBody.ALEXA_LF, CameraBody.ALEXA_MINI_LF} and
            c.lens.family in S35_ONLY_LENSES
        ),
    ),

    # --- LIGHTING PHYSICS ---
    Rule(
        rule_id="LA_NIGHT_NO_SUN",
        severity=RuleSeverity.HARD,
        message="Sunlight is not available at night.",
        field_path="lighting.source",
        check=lambda c: (
            c.lighting.time_of_day == TimeOfDay.NIGHT and
            c.lighting.source == LightingSource.SUN
        ),
    ),
    Rule(
        rule_id="LA_BLUEHOUR_NO_SUN",
        severity=RuleSeverity.HARD,
        message="Direct sunlight is not available during blue hour.",
        field_path="lighting.source",
        check=lambda c: (
            c.lighting.time_of_day == TimeOfDay.BLUE_HOUR and
            c.lighting.source == LightingSource.SUN
        ),
    ),
    Rule(
        rule_id="LA_MIDDAY_NO_LOWKEY",
        severity=RuleSeverity.HARD,
        message="Low-key lighting is nearly impossible at midday without extensive control.",
        field_path="lighting.style",
        check=lambda c: (
            c.lighting.time_of_day == TimeOfDay.MIDDAY and
            c.lighting.style == LightingStyle.LOW_KEY
        ),
    ),
    Rule(
        rule_id="LA_MIDDAY_NO_MOON",
        severity=RuleSeverity.HARD,
        message="Moonlight cannot be key light during midday.",
        field_path="lighting.source",
        check=lambda c: (
            c.lighting.time_of_day == TimeOfDay.MIDDAY and
            c.lighting.source == LightingSource.MOON
        ),
    ),

    # --- ERA ANACHRONISM ---
    Rule(
        rule_id="LA_ERA_HMI_ANACHRONISM",
        severity=RuleSeverity.HARD,
        message="HMI lighting was invented in 1972. Not available for earlier eras.",
        field_path="lighting.source",
        check=lambda c: (
            c.era is not None and
            _era_before_year(c.era, 1972) and
            c.lighting.source == LightingSource.HMI
        ),
    ),
    Rule(
        rule_id="LA_ERA_KINO_ANACHRONISM",
        severity=RuleSeverity.HARD,
        message="Kino Flo was founded in 1987. Not available for earlier eras.",
        field_path="lighting.source",
        check=lambda c: (
            c.era is not None and
            _era_before_year(c.era, 1987) and
            c.lighting.source == LightingSource.KINO_FLO
        ),
    ),
    Rule(
        rule_id="LA_ERA_LED_ANACHRONISM",
        severity=RuleSeverity.HARD,
        message="LED film lighting became available around 2002.",
        field_path="lighting.source",
        check=lambda c: (
            c.era is not None and
            _era_before_year(c.era, 2002) and
            c.lighting.source == LightingSource.LED
        ),
    ),

    # --- MOVEMENT CONSTRAINTS ---
    Rule(
        rule_id="LA_HEAVY_NO_HANDHELD",
        severity=RuleSeverity.HARD,
        message="Heavy cameras (>4kg) cannot be operated handheld safely.",
        field_path="movement.equipment",
        check=lambda c: (
            _get_weight_class(c.camera.body) == WeightClass.HEAVY and
            c.movement.equipment == MovementEquipment.HANDHELD
        ),
    ),
    Rule(
        rule_id="LA_HEAVY_NO_GIMBAL",
        severity=RuleSeverity.HARD,
        message="Heavy cameras (>4kg) exceed gimbal payload limits.",
        field_path="movement.equipment",
        check=lambda c: (
            _get_weight_class(c.camera.body) == WeightClass.HEAVY and
            c.movement.equipment == MovementEquipment.GIMBAL
        ),
    ),
    Rule(
        rule_id="LA_HEAVY_NO_DRONE",
        severity=RuleSeverity.HARD,
        message="Heavy cameras (>4kg) exceed standard drone payload limits.",
        field_path="movement.equipment",
        check=lambda c: (
            _get_weight_class(c.camera.body) == WeightClass.HEAVY and
            c.movement.equipment == MovementEquipment.DRONE
        ),
    ),
    Rule(
        rule_id="LA_JIB_MOVEMENT_RESTRICT",
        severity=RuleSeverity.HARD,
        message="Jib equipment can only perform Crane_Up, Crane_Down, and Arc movements.",
        field_path="movement.movement_type",
        check=lambda c: (
            c.movement.equipment == MovementEquipment.JIB and
            c.movement.movement_type not in {
                MovementType.CRANE_UP, MovementType.CRANE_DOWN,
                MovementType.ARC, MovementType.STATIC,
            }
        ),
    ),
    Rule(
        rule_id="LA_DOLLYZOOM_REQUIRES_DOLLY",
        severity=RuleSeverity.HARD,
        message="Dolly zoom (Vertigo effect) requires dolly or slider equipment.",
        field_path="movement.equipment",
        check=lambda c: (
            c.movement.movement_type == MovementType.DOLLY_ZOOM and
            c.movement.equipment not in {
                MovementEquipment.DOLLY, MovementEquipment.SLIDER,
            }
        ),
    ),

    # --- WARNINGS ---
    Rule(
        rule_id="LA_MEDIUM_HANDHELD_WARN",
        severity=RuleSeverity.WARNING,
        message="Medium-weight cameras (3-4kg) may cause operator fatigue during extended handheld work.",
        field_path="movement.equipment",
        check=lambda c: (
            _get_weight_class(c.camera.body) == WeightClass.MEDIUM and
            c.movement.equipment == MovementEquipment.HANDHELD
        ),
    ),
    Rule(
        rule_id="LA_WIDE_LENS_CU_WARN",
        severity=RuleSeverity.WARNING,
        message="Wide angle lens (<35mm) on close-up causes facial distortion. Intentional?",
        field_path="lens.focal_length_mm",
        check=lambda c: (
            c.lens.focal_length_mm < 35 and
            c.visual_grammar.shot_size.value in {"CU", "BCU", "ECU"}
        ),
    ),
    Rule(
        rule_id="LA_LONG_LENS_WIDE_WARN",
        severity=RuleSeverity.WARNING,
        message="Long lens (>85mm) on wide shot creates strong compression. Unusual choice.",
        field_path="lens.focal_length_mm",
        check=lambda c: (
            c.lens.focal_length_mm > 85 and
            c.visual_grammar.shot_size.value in {"EWS", "WS"}
        ),
    ),
    Rule(
        rule_id="LA_VINTAGE_HIGHRES_WARN",
        severity=RuleSeverity.WARNING,
        message="Vintage lenses may not resolve well on 8K+ sensors.",
        field_path="lens.family",
        check=lambda c: (
            c.lens.family in {LensFamily.VINTAGE_ANAMORPHIC, LensFamily.VINTAGE_SPHERICAL} and
            c.camera.body in HIGH_RES_CAMERAS
        ),
    ),
    Rule(
        rule_id="LA_CHEERFUL_LOWKEY_WARN",
        severity=RuleSeverity.WARNING,
        message="Cheerful mood with low-key lighting is atypical. Intentional subversion?",
        field_path="lighting.style",
        check=lambda c: (
            c.visual_grammar.mood == Mood.CHEERFUL and
            c.lighting.style == LightingStyle.LOW_KEY
        ),
    ),
    Rule(
        rule_id="LA_DOLLYZOOM_TIMING_WARN",
        severity=RuleSeverity.WARNING,
        message="Dolly zoom at fast timing is disorienting. Typically done at slow/moderate pace.",
        field_path="movement.timing",
        check=lambda c: (
            c.movement.movement_type == MovementType.DOLLY_ZOOM and
            c.movement.timing in {MovementTiming.FAST, MovementTiming.WHIP_FAST}
        ),
    ),

    # --- COMPOSITION CONSTRAINTS ---
    Rule(
        rule_id="LA_SYMMETRY_ECU_WARN",
        severity=RuleSeverity.WARNING,
        message="Symmetrical composition is unusual for ECU.",
        field_path="visual_grammar.composition",
        check=lambda c: (
            c.visual_grammar.composition == Composition.SYMMETRICAL and
            c.visual_grammar.shot_size == ShotSize.ECU
        ),
    ),
    Rule(
        rule_id="LA_FILL_FRAME_WIDE_WARN",
        severity=RuleSeverity.WARNING,
        message="Fill The Frame composition contradicts Wide Shot framing.",
        field_path="visual_grammar.composition",
        check=lambda c: (
            c.visual_grammar.composition == Composition.FILL_THE_FRAME and
            c.visual_grammar.shot_size in {ShotSize.WS, ShotSize.EWS, ShotSize.MWS}
        ),
    ),

    # --- INFO ---
    Rule(
        rule_id="LA_ANAMORPHIC_INFO",
        severity=RuleSeverity.INFO,
        message="Anamorphic lens selected. Set 2x de-squeeze in post for proper aspect ratio.",
        field_path="lens.is_anamorphic",
        check=lambda c: c.lens.is_anamorphic is True,
    ),
]


# =============================================================================
# PRESET DATA
# =============================================================================

LIVE_ACTION_PRESETS: dict[str, dict] = {
    "blade_runner_2049": {
        "name": "Blade Runner 2049",
        "dp": "Roger Deakins",
        "year": 2017,
        "camera": {"body": "Alexa_XT", "sensor": "Super35", "aspect_ratio": "2.39:1"},
        "lens": {"family": "ARRI_Master_Prime", "focal_length_mm": 40},
        "lighting": {"style": "Expressionistic", "source": "LED"},
        "visual_grammar": {"mood": "Ominous", "color_tone": "Cool_Desaturated"},
    },
    "dune_2021": {
        "name": "Dune (2021)",
        "dp": "Greig Fraser",
        "year": 2021,
        "camera": {"body": "Alexa_LF", "sensor": "LargeFormat", "aspect_ratio": "2.39:1"},
        "lens": {"family": "ARRI_Signature_Prime", "focal_length_mm": 35},
        "lighting": {"style": "Naturalistic", "source": "Sun"},
        "visual_grammar": {"mood": "Epic", "color_tone": "Warm_Desaturated"},
    },
    "mad_max_fury_road": {
        "name": "Mad Max: Fury Road",
        "dp": "John Seale",
        "year": 2015,
        "camera": {"body": "Alexa_XT", "sensor": "Super35", "aspect_ratio": "2.39:1"},
        "lens": {"family": "ARRI_Ultra_Prime", "focal_length_mm": 21},
        "lighting": {"style": "Naturalistic", "source": "Sun"},
        "visual_grammar": {"mood": "Chaotic", "color_tone": "Warm_Saturated"},
    },
    "interstellar": {
        "name": "Interstellar",
        "dp": "Hoyte van Hoytema",
        "year": 2014,
        "camera": {"body": "IMAX_MSM_9802", "sensor": "IMAX_15_70", "film_stock": "IMAX_500T", "aspect_ratio": "1.43:1"},
        "lens": {"family": "IMAX_Optics", "focal_length_mm": 50},
        "lighting": {"style": "Naturalistic", "source": "Sun"},
        "visual_grammar": {"mood": "Epic", "color_tone": "Neutral_Saturated"},
    },
    "parasite": {
        "name": "Parasite (기생충)",
        "dp": "Hong Kyung-pyo",
        "year": 2019,
        "camera": {"body": "Alexa_65", "sensor": "65mm", "aspect_ratio": "2.39:1"},
        "lens": {"family": "ARRI_Prime_65", "focal_length_mm": 50},
        "lighting": {"style": "Motivated", "source": "Window"},
        "visual_grammar": {"mood": "Tense", "color_tone": "Neutral_Saturated"},
    },
    "the_godfather": {
        "name": "The Godfather",
        "dp": "Gordon Willis",
        "year": 1972,
        "camera": {"body": "Arricam_ST", "sensor": "Film_35mm", "film_stock": "Eastman_5254", "aspect_ratio": "1.85:1"},
        "lens": {"family": "Bausch_Lomb_Baltar", "focal_length_mm": 40},
        "lighting": {"style": "Low_Key", "source": "Practical"},
        "visual_grammar": {"mood": "Ominous", "color_tone": "Warm_Desaturated"},
        "era": "1970s",
    },
    "in_the_mood_for_love": {
        "name": "In the Mood for Love (花樣年華)",
        "dp": "Christopher Doyle",
        "year": 2000,
        "camera": {"body": "ARRI_535B", "sensor": "Film_35mm", "film_stock": "Kodak_Vision3_500T_5219", "aspect_ratio": "1.66:1"},
        "lens": {"family": "Cooke_Speed_Panchro", "focal_length_mm": 50},
        "lighting": {"style": "Practical_Motivated", "source": "Practical"},
        "visual_grammar": {"mood": "Melancholic", "color_tone": "Warm_Saturated"},
    },
    "oldboy": {
        "name": "Oldboy (올드보이)",
        "dp": "Chung Chung-hoon",
        "year": 2003,
        "camera": {"body": "Arricam_LT", "sensor": "Film_35mm", "film_stock": "Kodak_Vision3_500T_5219", "aspect_ratio": "2.39:1"},
        "lens": {"family": "Zeiss_Ultra_Prime", "focal_length_mm": 28},
        "lighting": {"style": "Expressionistic", "source": "Fluorescent"},
        "visual_grammar": {"mood": "Gritty", "color_tone": "Cool_Desaturated"},
    },
    "no_country_for_old_men": {
        "name": "No Country for Old Men",
        "dp": "Roger Deakins",
        "year": 2007,
        "camera": {"body": "Arricam_ST", "sensor": "Film_35mm", "film_stock": "Kodak_Vision3_250D_5207", "aspect_ratio": "1.85:1"},
        "lens": {"family": "ARRI_Master_Prime", "focal_length_mm": 35},
        "lighting": {"style": "Naturalistic", "source": "Available_Light"},
        "visual_grammar": {"mood": "Tense", "color_tone": "Warm_Desaturated"},
    },
    "the_revenant": {
        "name": "The Revenant",
        "dp": "Emmanuel Lubezki",
        "year": 2015,
        "camera": {"body": "Alexa_65", "sensor": "65mm", "aspect_ratio": "2.39:1"},
        "lens": {"family": "ARRI_Prime_65", "focal_length_mm": 12},
        "lighting": {"style": "Naturalistic", "source": "Available_Light"},
        "visual_grammar": {"mood": "Raw", "color_tone": "Cool_Desaturated"},
    },
    "joker": {
        "name": "Joker",
        "dp": "Lawrence Sher",
        "year": 2019,
        "camera": {"body": "Alexa_LF", "sensor": "LargeFormat", "aspect_ratio": "1.85:1"},
        "lens": {"family": "ARRI_Signature_Prime", "focal_length_mm": 40},
        "lighting": {"style": "Hard_Lighting", "source": "Tungsten"},
        "visual_grammar": {"mood": "Gritty", "color_tone": "Teal_Orange"},
    },
    "neon_cyberpunk": {
        "name": "Neon Cyberpunk",
        "dp": "Generic",
        "year": 2025,
        "camera": {"body": "Venice_2", "sensor": "FullFrame", "aspect_ratio": "2.39:1"},
        "lens": {"family": "Cooke_Anamorphic", "focal_length_mm": 50, "is_anamorphic": True},
        "lighting": {"style": "Expressionistic", "source": "Neon"},
        "visual_grammar": {"mood": "Ominous", "color_tone": "Teal_Orange"},
    },
}

ANIMATION_PRESETS: dict[str, dict] = {
    "ghibli_classic": {
        "name": "Studio Ghibli Classic",
        "medium": "2D",
        "style_domain": "Anime",
        "rendering": {
            "line_treatment": "Clean",
            "color_application": "Cel",
            "lighting_model": "Naturalistic_Simulated",
            "surface_detail": "Painterly",
        },
        "motion": {"motion_style": "Full", "virtual_camera": "Parallax"},
        "visual_grammar": {"mood": "Warm", "color_tone": "Warm_Saturated"},
    },
    "makoto_shinkai": {
        "name": "Makoto Shinkai Style",
        "medium": "2D",
        "style_domain": "Anime",
        "rendering": {
            "line_treatment": "Clean",
            "color_application": "Soft",
            "lighting_model": "Glow",
            "surface_detail": "Painterly",
        },
        "motion": {"motion_style": "Fluid", "virtual_camera": "Digital_Pan"},
        "visual_grammar": {"mood": "Dreamy", "color_tone": "Warm_Saturated"},
    },
    "akira": {
        "name": "Akira (1988)",
        "medium": "2D",
        "style_domain": "Anime",
        "rendering": {
            "line_treatment": "Variable",
            "color_application": "Cel",
            "lighting_model": "Glow_Emission",
            "surface_detail": "Textured",
        },
        "motion": {"motion_style": "Full", "virtual_camera": "Free_3D"},
        "visual_grammar": {"mood": "Chaotic", "color_tone": "Cool_Saturated"},
    },
    "spider_verse": {
        "name": "Spider-Verse Style",
        "medium": "Hybrid",
        "style_domain": "Western_Animation",
        "rendering": {
            "line_treatment": "Inked",
            "color_application": "Flat",
            "lighting_model": "Dramatic",
            "surface_detail": "Hatched",
        },
        "motion": {"motion_style": "Snappy", "virtual_camera": "Free_3D"},
        "visual_grammar": {"mood": "Energetic", "color_tone": "Warm_Saturated"},
    },
    "arcane": {
        "name": "Arcane (Fortiche)",
        "medium": "Hybrid",
        "style_domain": "Western_Animation",
        "rendering": {
            "line_treatment": "Sketchy",
            "color_application": "Painterly",
            "lighting_model": "Dramatic",
            "surface_detail": "Painterly",
        },
        "motion": {"motion_style": "Fluid", "virtual_camera": "Free_3D"},
        "visual_grammar": {"mood": "Dramatic", "color_tone": "Teal_Orange"},
    },
    "pixar_style": {
        "name": "Pixar Style",
        "medium": "3D",
        "style_domain": "ThreeD",
        "rendering": {
            "line_treatment": "None",
            "color_application": "Full",
            "lighting_model": "Naturalistic_Simulated",
            "surface_detail": "Smooth",
        },
        "motion": {"motion_style": "Exaggerated", "virtual_camera": "Free_3D"},
        "visual_grammar": {"mood": "Cheerful", "color_tone": "Warm_Saturated"},
    },
    "junji_ito": {
        "name": "Junji Ito Horror Manga",
        "medium": "2D",
        "style_domain": "Manga",
        "rendering": {
            "line_treatment": "Inked",
            "color_application": "Monochrome_Ink",
            "lighting_model": "Dramatic",
            "surface_detail": "Hatched",
        },
        "motion": {"motion_style": "None", "virtual_camera": "Locked"},
        "visual_grammar": {"mood": "Terrifying", "color_tone": "High_Contrast_BW"},
    },
}


# =============================================================================
# RULE ENGINE
# =============================================================================

class RuleEngine:
    """Core rule engine — validates configurations and enforces constraints."""

    def __init__(self):
        self._live_action_rules = LIVE_ACTION_RULES
        self._animation_rules: list[Rule] = []  # Animation rules can be added later
        logger.info(
            f"RuleEngine initialized: {len(self._live_action_rules)} live-action rules, "
            f"{len(self._animation_rules)} animation rules"
        )

    def validate_live_action(self, config: LiveActionConfig) -> ValidationResult:
        """Validate a live-action configuration against all rules."""
        messages = []
        for rule in self._live_action_rules:
            msg = rule.evaluate(config)
            if msg:
                messages.append(msg)

        if any(m.severity == RuleSeverity.HARD for m in messages):
            status = "invalid"
        elif any(m.severity == RuleSeverity.WARNING for m in messages):
            status = "warning"
        else:
            status = "valid"

        return ValidationResult(status=status, messages=messages)

    def validate_animation(self, config: AnimationConfig) -> ValidationResult:
        """Validate an animation configuration."""
        messages = []
        for rule in self._animation_rules:
            msg = rule.evaluate(config)
            if msg:
                messages.append(msg)

        if any(m.severity == RuleSeverity.HARD for m in messages):
            status = "invalid"
        elif any(m.severity == RuleSeverity.WARNING for m in messages):
            status = "warning"
        else:
            status = "valid"

        return ValidationResult(status=status, messages=messages)

    def validate_shot_list(
        self, configs: list[LiveActionConfig]
    ) -> dict[int, ValidationResult]:
        """Batch validate an entire shot list. Returns {index: result}."""
        results = {}
        for i, config in enumerate(configs):
            results[i] = self.validate_live_action(config)
        invalid_count = sum(1 for r in results.values() if r.status == "invalid")
        if invalid_count > 0:
            logger.warning(f"Shot list validation: {invalid_count}/{len(configs)} shots have errors")
        return results

    def get_preset(self, preset_id: str) -> dict | None:
        """Get a preset by ID from live-action or animation presets."""
        if preset_id in LIVE_ACTION_PRESETS:
            return LIVE_ACTION_PRESETS[preset_id]
        if preset_id in ANIMATION_PRESETS:
            return ANIMATION_PRESETS[preset_id]
        return None

    def list_presets(self) -> dict:
        """List all available presets."""
        return {
            "live_action": {
                k: {"name": v["name"], "year": v.get("year"), "dp": v.get("dp")}
                for k, v in LIVE_ACTION_PRESETS.items()
            },
            "animation": {
                k: {"name": v["name"], "medium": v.get("medium")}
                for k, v in ANIMATION_PRESETS.items()
            },
        }

    def get_rule_count(self) -> dict:
        """Return count of registered rules by severity."""
        counts = {"hard": 0, "warning": 0, "info": 0, "total": 0}
        for rule in self._live_action_rules + self._animation_rules:
            counts[rule.severity.value] += 1
            counts["total"] += 1
        return counts
