"""
Cinema Prompt Engineering (CPE) — Enum Definitions.

All enums for camera, lens, film stock, lighting, movement, shot, composition,
mood, and animation systems. Referenced from DirectorsConsole but restructured
for our pipeline-first architecture.
"""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# =============================================================================
# SHARED ENUMS — Visual Grammar (Live-Action + Animation)
# =============================================================================

class ShotSize(str, Enum):
    """Shot sizes — shared across Live-Action and Animation."""
    EWS = "EWS"          # Extreme Wide Shot
    WS = "WS"            # Wide Shot
    MWS = "MWS"          # Medium Wide Shot
    MS = "MS"            # Medium Shot
    MCU = "MCU"          # Medium Close Up
    CU = "CU"            # Close Up
    BCU = "BCU"          # Big Close Up
    ECU = "ECU"          # Extreme Close Up
    OTS = "OTS"          # Over The Shoulder
    POV = "POV"          # Point of View
    AMERICAN = "American"  # Cowboy shot (knees up)
    ITALIAN = "Italian"    # Eyes only


class Composition(str, Enum):
    """Composition techniques."""
    RULE_OF_THIRDS = "Rule_of_Thirds"
    CENTERED = "Centered"
    SYMMETRICAL = "Symmetrical"
    ASYMMETRICAL = "Asymmetrical"
    GOLDEN_RATIO = "Golden_Ratio"
    DIAGONAL = "Diagonal"
    DUTCH_ANGLE = "Dutch_Angle"
    LEADING_LINES = "Leading_Lines"
    FRAME_WITHIN_FRAME = "Frame_within_Frame"
    DEPTH_LAYERING = "Depth_Layering"
    NEGATIVE_SPACE = "Negative_Space"
    FILL_THE_FRAME = "Fill_the_Frame"
    FOREGROUND_FRAMING = "Foreground_Framing"
    SPLIT_SCREEN = "Split_Screen"
    OVERHEAD = "Overhead"
    WORMS_EYE = "Worms_Eye"
    BIRDS_EYE = "Birds_Eye"
    LOW_ANGLE = "Low_Angle"
    HIGH_ANGLE = "High_Angle"


class Mood(str, Enum):
    """Emotional mood/tone."""
    CHEERFUL = "Cheerful"
    HOPEFUL = "Hopeful"
    WHIMSICAL = "Whimsical"
    ROMANTIC = "Romantic"
    EUPHORIC = "Euphoric"
    SERENE = "Serene"
    CONTEMPLATIVE = "Contemplative"
    MELANCHOLIC = "Melancholic"
    NOSTALGIC = "Nostalgic"
    GLOOMY = "Gloomy"
    TENSE = "Tense"
    SUSPENSEFUL = "Suspenseful"
    OMINOUS = "Ominous"
    TERRIFYING = "Terrifying"
    UNSETTLING = "Unsettling"
    MYSTERIOUS = "Mysterious"
    EPIC = "Epic"
    HEROIC = "Heroic"
    TRIUMPHANT = "Triumphant"
    DRAMATIC = "Dramatic"
    INTIMATE = "Intimate"
    SURREAL = "Surreal"
    DREAMY = "Dreamy"
    ETHEREAL = "Ethereal"
    GRITTY = "Gritty"
    RAW = "Raw"
    COLD = "Cold"
    WARM = "Warm"
    ENERGETIC = "Energetic"
    CHAOTIC = "Chaotic"
    PEACEFUL = "Peaceful"
    DESOLATE = "Desolate"


class ColorTone(str, Enum):
    """Color temperature and saturation."""
    WARM_SATURATED = "Warm_Saturated"
    WARM_DESATURATED = "Warm_Desaturated"
    COOL_SATURATED = "Cool_Saturated"
    COOL_DESATURATED = "Cool_Desaturated"
    NEUTRAL_SATURATED = "Neutral_Saturated"
    NEUTRAL_DESATURATED = "Neutral_Desaturated"
    MONOCHROME = "Monochrome"
    SEPIA = "Sepia"
    TEAL_ORANGE = "Teal_Orange"
    CROSS_PROCESSED = "Cross_Processed"
    BLEACH_BYPASS = "Bleach_Bypass"
    HIGH_CONTRAST_BW = "High_Contrast_BW"
    LOW_CONTRAST_BW = "Low_Contrast_BW"


class ProjectType(str, Enum):
    """Top-level project type."""
    LIVE_ACTION = "live_action"
    ANIMATION = "animation"


class VisualGrammar(BaseModel):
    """Visual grammar — shared structure between Live-Action and Animation."""
    shot_size: ShotSize = ShotSize.MS
    composition: Composition = Composition.RULE_OF_THIRDS
    mood: Mood = Mood.CONTEMPLATIVE
    color_tone: ColorTone = ColorTone.NEUTRAL_SATURATED


# =============================================================================
# CAMERA SYSTEM
# =============================================================================

class CameraType(str, Enum):
    DIGITAL = "Digital"
    FILM = "Film"


class CameraManufacturer(str, Enum):
    # Digital
    ARRI = "ARRI"
    RED = "RED"
    SONY = "Sony"
    CANON = "Canon"
    BLACKMAGIC = "Blackmagic"
    PANASONIC = "Panasonic"
    NIKON = "Nikon"
    DJI = "DJI"
    # Film
    ARRI_FILM = "ARRI_Film"
    PANAVISION = "Panavision"
    MITCHELL = "Mitchell"
    IMAX_CORP = "IMAX"
    ECLAIR = "Eclair"
    VINTAGE = "Vintage"


class SensorSize(str, Enum):
    SUPER35 = "Super35"
    FULL_FRAME = "FullFrame"
    LARGE_FORMAT = "LargeFormat"
    SIXTY_FIVE_MM = "65mm"
    MICRO_FOUR_THIRDS = "MicroFourThirds"
    FILM_35MM = "Film_35mm"
    FILM_65MM = "Film_65mm"
    FILM_70MM = "Film_70mm"
    IMAX_15_70 = "IMAX_15_70"
    IMAX_GT = "IMAX_GT"


class WeightClass(str, Enum):
    """Camera weight classification for movement constraints."""
    ULTRA_LIGHT = "UltraLight"  # < 2.0 kg
    LIGHT = "Light"             # 2.0 - 3.0 kg
    MEDIUM = "Medium"           # 3.0 - 4.0 kg
    HEAVY = "Heavy"             # > 4.0 kg


class CameraBody(str, Enum):
    """Camera models — 49 bodies covering major cinema cameras."""
    # ARRI Digital
    ALEXA_35 = "Alexa_35"
    ALEXA_MINI = "Alexa_Mini"
    ALEXA_MINI_LF = "Alexa_Mini_LF"
    ALEXA_LF = "Alexa_LF"
    ALEXA_65 = "Alexa_65"
    ALEXA = "Alexa"
    ALEXA_XT = "Alexa_XT"
    # RED
    V_RAPTOR = "V_Raptor"
    V_RAPTOR_X = "V_Raptor_X"
    V_RAPTOR_XL = "V_Raptor_XL"
    KOMODO_X = "Komodo_X"
    MONSTRO_8K = "Monstro_8K"
    RED_ONE = "RED_One"
    # Sony
    VENICE_2 = "Venice_2"
    FX9 = "FX9"
    FX6 = "FX6"
    # Canon
    C700_FF = "C700_FF"
    C500_MARK_II = "C500_Mark_II"
    C300_MARK_III = "C300_Mark_III"
    # Blackmagic
    URSA_MINI_PRO_12K = "Ursa_Mini_Pro_12K"
    POCKET_6K = "Pocket_6K"
    # Panasonic
    VARICAM_LT = "Varicam_LT"
    S1H = "S1H"
    # Nikon
    Z9 = "Z9"
    # DJI
    INSPIRE_3 = "Inspire_3"
    MAVIC_3_CINE = "Mavic_3_Cine"
    # ARRI Film
    ARRICAM_ST = "Arricam_ST"
    ARRICAM_LT = "Arricam_LT"
    ARRI_535B = "ARRI_535B"
    ARRI_35BL = "ARRI_35BL"
    ARRI_35_III = "ARRI_35_III"
    ARRIFLEX_35 = "Arriflex_35"
    ARRIFLEX_35BL = "Arriflex_35BL"
    ARRIFLEX_435 = "Arriflex_435"
    # Eclair
    ECLAIR_NPR = "Eclair_NPR"
    # Panavision Film
    PANAVISION_MILLENNIUM_XL2 = "Panavision_Millennium_XL2"
    PANAVISION_MILLENNIUM = "Panavision_Millennium"
    PANAVISION_PLATINUM = "Panavision_Platinum"
    PANAVISION_GOLD = "Panavision_Gold"
    PANAVISION_PANASTAR = "Panavision_Panastar"
    PANAVISION_PANAFLEX = "Panavision_Panaflex"
    SUPER_PANAVISION_70 = "Super_Panavision_70"
    ULTRA_PANAVISION_70 = "Ultra_Panavision_70"
    PANAVISION_XL = "Panavision_XL"
    # Mitchell
    MITCHELL_BNC = "Mitchell_BNC"
    MITCHELL_BNCR = "Mitchell_BNCR"
    MITCHELL_BFC_65 = "Mitchell_BFC_65"
    # IMAX
    IMAX_MSM_9802 = "IMAX_MSM_9802"
    IMAX_MKIV = "IMAX_MKIV"
    IMAX_GT_BODY = "IMAX_GT"
    # Vintage
    UFA_CUSTOM = "UFA_Custom"
    PATHE_STUDIO = "Pathe_Studio"


# =============================================================================
# LENS SYSTEM
# =============================================================================

class LensManufacturer(str, Enum):
    ARRI = "ARRI"
    ZEISS = "Zeiss"
    COOKE = "Cooke"
    PANAVISION = "Panavision"
    LEICA = "Leica"
    CANON = "Canon"
    SIGMA = "Sigma"
    ANGENIEUX = "Angenieux"
    SONY = "Sony"
    FUJIFILM = "Fujifilm"
    HAWK = "Hawk"
    HASSELBLAD = "Hasselblad"
    TECHNOVISION = "Technovision"
    BAUSCH_LOMB = "Bausch_Lomb"
    TODD_AO = "Todd_AO"
    KOWA = "Kowa"
    VINTAGE = "Vintage"


class LensFamily(str, Enum):
    """Lens families — 47 series covering major cine lenses."""
    # ARRI
    ARRI_SIGNATURE_PRIME = "ARRI_Signature_Prime"
    ARRI_MASTER_PRIME = "ARRI_Master_Prime"
    ARRI_ULTRA_PRIME = "ARRI_Ultra_Prime"
    ARRI_PRIME_65 = "ARRI_Prime_65"
    ARRI_PRIME_DNA = "ARRI_Prime_DNA"
    # Zeiss
    ZEISS_SUPREME_PRIME = "Zeiss_Supreme_Prime"
    ZEISS_MASTER_PRIME = "Zeiss_Master_Prime"
    ZEISS_CP3 = "Zeiss_CP3"
    ZEISS_SUPER_SPEED = "Zeiss_Super_Speed"
    ZEISS_STANDARD_SPEED = "Zeiss_Standard_Speed"
    ZEISS_ULTRA_PRIME = "Zeiss_Ultra_Prime"
    ZEISS_PLANAR = "Zeiss_Planar"
    ZEISS_PLANAR_F07 = "Zeiss_Planar_f0.7"
    # Cooke
    COOKE_S7 = "Cooke_S7"
    COOKE_S4 = "Cooke_S4"
    COOKE_ANAMORPHIC = "Cooke_Anamorphic"
    COOKE_PANCHRO = "Cooke_Panchro"
    COOKE_SPEED_PANCHRO = "Cooke_Speed_Panchro"
    # Panavision
    PANAVISION_PRIMO = "Panavision_Primo"
    PANAVISION_PRIMO_70 = "Panavision_Primo_70"
    PANAVISION_ANAMORPHIC = "Panavision_Anamorphic"
    PANAVISION_C_SERIES = "Panavision_C_Series"
    PANAVISION_E_SERIES = "Panavision_E_Series"
    PANAVISION_SPHERO = "Panavision_Sphero"
    PANAVISION_ULTRA_SPEED = "Panavision_Ultra_Speed"
    # Leica
    LEICA_SUMMILUX = "Leica_Summilux"
    LEICA_SUMMICRON = "Leica_Summicron"
    LEICA_THALIA = "Leica_Thalia"
    # Canon
    CANON_SUMIRE = "Canon_Sumire"
    CANON_CN_E = "Canon_CN_E"
    CANON_K35 = "Canon_K35"
    # Sony
    SONY_CINEALTA = "Sony_CineAlta"
    # Sigma
    SIGMA_CINE = "Sigma_Cine"
    SIGMA_HIGH_SPEED = "Sigma_High_Speed"
    # Angenieux
    ANGENIEUX_OPTIMO = "Angenieux_Optimo"
    ANGENIEUX_EZ = "Angenieux_EZ"
    ANGENIEUX_HR = "Angenieux_HR"
    # Vintage
    BAUSCH_LOMB_SUPER_BALTAR = "Bausch_Lomb_Super_Baltar"
    BAUSCH_LOMB_BALTAR = "Bausch_Lomb_Baltar"
    TODD_AO = "Todd_AO"
    HAWK_V_LITE = "Hawk_V_Lite"
    HAWK_V_PLUS = "Hawk_V_Plus"
    HASSELBLAD_HC = "Hasselblad_HC"
    HASSELBLAD_V = "Hasselblad_V"
    IMAX_OPTICS = "IMAX_Optics"
    VINTAGE_ANAMORPHIC = "Vintage_Anamorphic"
    VINTAGE_SPHERICAL = "Vintage_Spherical"


class LensMountType(str, Enum):
    PL = "PL"
    LPL = "LPL"
    XPL = "XPL"
    PANAVISION = "Panavision"
    MITCHELL_BNC = "Mitchell_BNC"
    IMAX = "IMAX"


# =============================================================================
# FILM STOCK SYSTEM
# =============================================================================

class FilmStock(str, Enum):
    """Film stocks — 31 types from Kodak, Fuji, IMAX."""
    # Vision3 (Current)
    KODAK_VISION3_500T = "Kodak_Vision3_500T_5219"
    KODAK_VISION3_250D = "Kodak_Vision3_250D_5207"
    KODAK_VISION3_200T = "Kodak_Vision3_200T_5213"
    KODAK_VISION3_50D = "Kodak_Vision3_50D_5203"
    # Vision2
    KODAK_VISION2_500T = "Kodak_Vision2_500T_5218"
    KODAK_VISION2_200T = "Kodak_Vision2_200T_5217"
    # Vision
    KODAK_VISION_500T = "Kodak_Vision_500T_5279"
    KODAK_VISION_320T = "Kodak_Vision_320T_5277"
    # B&W
    KODAK_DOUBLE_X = "Kodak_Double_X_5222"
    KODAK_TRI_X = "Kodak_Tri_X"
    EASTMAN_DOUBLE_X = "Eastman_Double_X"
    EASTMAN_PLUS_X = "Eastman_Plus_X"
    # Historic
    EASTMAN_5247 = "Eastman_5247"
    EASTMAN_5293 = "Eastman_5293"
    EASTMAN_5294 = "Eastman_5294"
    EASTMAN_5250 = "Eastman_5250"
    EASTMAN_5254 = "Eastman_5254"
    TECHNICOLOR = "Technicolor"
    KODACHROME = "Kodachrome"
    # Fuji
    FUJI_ETERNA_500T = "Fuji_Eterna_500T"
    FUJI_ETERNA_250D = "Fuji_Eterna_250D"
    FUJI_ETERNA_250T = "Fuji_Eterna_250T"
    # 65mm
    KODAK_65MM_500T = "Kodak_65mm_500T"
    KODAK_65MM_250D = "Kodak_65mm_250D"
    KODAK_65MM_200T = "Kodak_65mm_200T"
    # IMAX
    IMAX_500T = "IMAX_500T"
    IMAX_250D = "IMAX_250D"
    # N/A
    NONE = "None"


class AspectRatio(str, Enum):
    """Aspect ratios — constrained by camera format."""
    RATIO_1_33 = "1.33:1"   # Academy (4:3)
    RATIO_1_37 = "1.37:1"   # Academy Sound
    RATIO_1_66 = "1.66:1"   # European Widescreen
    RATIO_1_78 = "1.78:1"   # 16:9 HD
    RATIO_1_85 = "1.85:1"   # American Widescreen
    RATIO_2_20 = "2.20:1"   # 70mm Standard
    RATIO_2_35 = "2.35:1"   # CinemaScope
    RATIO_2_39 = "2.39:1"   # Panavision Scope
    RATIO_2_76 = "2.76:1"   # Ultra Panavision 70
    RATIO_1_43 = "1.43:1"   # IMAX 15/70
    RATIO_1_90 = "1.90:1"   # IMAX Digital


# =============================================================================
# CAMERA MOVEMENT
# =============================================================================

class MovementEquipment(str, Enum):
    STATIC = "Static"
    HANDHELD = "Handheld"
    SHOULDER_RIG = "Shoulder_Rig"
    STEADICAM = "Steadicam"
    GIMBAL = "Gimbal"
    DOLLY = "Dolly"
    DOLLY_TRACK = "Dolly_Track"
    SLIDER = "Slider"
    CRANE = "Crane"
    JIB = "Jib"
    TECHNOCRANE = "Technocrane"
    MOTION_CONTROL = "Motion_Control"
    DRONE = "Drone"
    CABLE_CAM = "Cable_Cam"
    CAR_MOUNT = "Car_Mount"
    SNORRICAM = "SnorriCam"


class MovementType(str, Enum):
    STATIC = "Static"
    PAN = "Pan"
    TILT = "Tilt"
    PAN_TILT = "Pan_Tilt"
    TRACK_IN = "Track_In"
    TRACK_OUT = "Track_Out"
    PUSH_IN = "Push_In"
    PULL_BACK = "Pull_Back"
    TRUCK_LEFT = "Truck_Left"
    TRUCK_RIGHT = "Truck_Right"
    CRAB = "Crab"
    ARC = "Arc"
    CRANE_UP = "Crane_Up"
    CRANE_DOWN = "Crane_Down"
    BOOM_UP = "Boom_Up"
    BOOM_DOWN = "Boom_Down"
    DOLLY_ZOOM = "Dolly_Zoom"
    PUSH_PULL = "Push_Pull"
    ZOOM_IN = "Zoom_In"
    ZOOM_OUT = "Zoom_Out"
    CRASH_ZOOM = "Crash_Zoom"
    ROLL = "Roll"
    WHIP_PAN = "Whip_Pan"
    WHIP_TILT = "Whip_Tilt"
    FOLLOW = "Follow"
    LEAD = "Lead"
    ORBIT = "Orbit"
    REVEAL = "Reveal"
    FLY_THROUGH = "Fly_Through"


class MovementTiming(str, Enum):
    STATIC = "Static"
    VERY_SLOW = "Very_Slow"
    SLOW = "Slow"
    MODERATE = "Moderate"
    FAST = "Fast"
    WHIP_FAST = "Whip_Fast"


# =============================================================================
# LIGHTING SYSTEM
# =============================================================================

class TimeOfDay(str, Enum):
    DAWN = "Dawn"
    MORNING = "Morning"
    MIDDAY = "Midday"
    AFTERNOON = "Afternoon"
    GOLDEN_HOUR = "Golden_Hour"
    BLUE_HOUR = "Blue_Hour"
    DUSK = "Dusk"
    NIGHT = "Night"
    MAGIC_HOUR = "Magic_Hour"


class LightingSource(str, Enum):
    # Natural
    SUN = "Sun"
    MOON = "Moon"
    OVERCAST = "Overcast"
    WINDOW = "Window"
    SKYLIGHT = "Skylight"
    # Modern artificial
    TUNGSTEN = "Tungsten"
    HMI = "HMI"                    # 1972+
    LED = "LED"                    # 2002+
    KINO_FLO = "Kino_Flo"          # 1987+
    NEON = "Neon"                  # 1927+
    FLUORESCENT = "Fluorescent"
    ARTIFICIAL = "Artificial"
    # Historic
    CARBON_ARC = "Carbon_Arc"      # 1895-1960s
    MERCURY_VAPOR = "Mercury_Vapor"  # 1903+
    SODIUM_VAPOR = "Sodium_Vapor"    # 1930s+
    # Practical
    PRACTICAL = "Practical"
    PRACTICAL_LIGHTS = "Practical_Lights"
    CANDLE = "Candle"
    CANDLELIGHT = "Candlelight"
    FIRELIGHT = "Firelight"
    TELEVISION = "Television"
    COMPUTER_SCREEN = "Computer_Screen"
    # Mixed
    MIXED = "Mixed"
    AVAILABLE = "Available"
    AVAILABLE_LIGHT = "Available_Light"


class LightingStyle(str, Enum):
    HIGH_KEY = "High_Key"
    LOW_KEY = "Low_Key"
    SOFT = "Soft"
    SOFT_LIGHTING = "Soft_Lighting"
    HARD = "Hard"
    HARD_LIGHTING = "Hard_Lighting"
    NATURALISTIC = "Naturalistic"
    EXPRESSIONISTIC = "Expressionistic"
    CHIAROSCURO = "Chiaroscuro"
    REMBRANDT = "Rembrandt"
    SPLIT = "Split"
    RIM = "Rim"
    SILHOUETTE = "Silhouette"
    MOTIVATED = "Motivated"
    PRACTICAL_MOTIVATED = "Practical_Motivated"
    AVAILABLE_LIGHT = "Available_Light"
    HIGH_CONTRAST = "High_Contrast"
    CONTROLLED = "Controlled"
    FLAT = "Flat"
    DRAMATIC = "Dramatic"


# =============================================================================
# ANIMATION SYSTEM
# =============================================================================

class AnimationMedium(str, Enum):
    TWO_D = "2D"
    THREE_D = "3D"
    HYBRID = "Hybrid"
    STOP_MOTION = "StopMotion"


class StyleDomain(str, Enum):
    ANIME = "Anime"
    MANGA = "Manga"
    THREE_D = "ThreeD"
    ILLUSTRATION = "Illustration"
    WESTERN_ANIMATION = "Western_Animation"
    GRAPHIC_NOVEL = "Graphic_Novel"
    PAINTERLY = "Painterly"
    CONCEPT_ART = "Concept_Art"


class LineTreatment(str, Enum):
    CLEAN = "Clean"
    VARIABLE = "Variable"
    INKED = "Inked"
    SKETCHY = "Sketchy"
    NONE = "None"


class ColorApplication(str, Enum):
    FLAT = "Flat"
    CEL = "Cel"
    SOFT = "Soft"
    PAINTERLY = "Painterly"
    MONOCHROME = "Monochrome"
    MONOCHROME_INK = "Monochrome_Ink"
    LIMITED = "Limited"
    FULL = "Full"


class AnimLightingModel(str, Enum):
    """Animation-specific lighting approach."""
    SYMBOLIC = "Symbolic"
    GRAPHIC = "Graphic"
    GRAPHIC_LIGHT = "Graphic_Light"
    NATURALISTIC_SIMULATED = "Naturalistic_Simulated"
    STYLIZED_RIM = "Stylized_Rim"
    GLOW = "Glow"
    GLOW_EMISSION = "Glow_Emission"
    MINIMAL = "Minimal"
    FLAT_LIGHT = "Flat_Light"
    DRAMATIC = "Dramatic"


class SurfaceDetail(str, Enum):
    FLAT = "Flat"
    PAINTERLY = "Painterly"
    SMOOTH = "Smooth"
    PHOTOREAL = "Photoreal"
    TEXTURED = "Textured"
    HATCHED = "Hatched"


class MotionStyle(str, Enum):
    NONE = "None"
    LIMITED = "Limited"
    FULL = "Full"
    EXAGGERATED = "Exaggerated"
    SNAPPY = "Snappy"
    FLUID = "Fluid"
    ROTOSCOPED = "Rotoscoped"


class VirtualCamera(str, Enum):
    LOCKED = "Locked"
    DIGITAL_PAN = "Digital_Pan"
    DIGITAL_ZOOM = "Digital_Zoom"
    PARALLAX = "Parallax"
    FREE_3D = "Free_3D"
    SIMULATED_HANDHELD = "Simulated_Handheld"
    MOTION_COMIC = "Motion_Comic"


# =============================================================================
# VALIDATION
# =============================================================================

class RuleSeverity(str, Enum):
    HARD = "hard"
    WARNING = "warning"
    INFO = "info"


class ValidationMessage(BaseModel):
    """A single validation message from the rule engine."""
    rule_id: str
    severity: RuleSeverity
    message: str
    field_path: str | None = None


class ValidationResult(BaseModel):
    """Result of validating a configuration."""
    status: Literal["valid", "warning", "invalid"]
    messages: list[ValidationMessage] = Field(default_factory=list)
    auto_corrections_applied: bool = False


# =============================================================================
# CONFIG MODELS (Composed from enums)
# =============================================================================

class CameraConfig(BaseModel):
    """Camera selection for a shot."""
    camera_type: CameraType = CameraType.DIGITAL
    manufacturer: CameraManufacturer = CameraManufacturer.ARRI
    body: CameraBody = CameraBody.ALEXA_35
    sensor: SensorSize = SensorSize.SUPER35
    weight_class: WeightClass = WeightClass.MEDIUM
    film_stock: FilmStock = FilmStock.NONE
    aspect_ratio: AspectRatio = AspectRatio.RATIO_2_39


class LensConfig(BaseModel):
    """Lens selection for a shot."""
    manufacturer: LensManufacturer = LensManufacturer.ARRI
    family: LensFamily = LensFamily.ARRI_SIGNATURE_PRIME
    focal_length_mm: int = Field(default=50, ge=8, le=1200)
    is_anamorphic: bool = False
    squeeze_ratio: float | None = Field(default=None, description="Anamorphic squeeze (e.g., 2.0)")


class MovementConfig(BaseModel):
    """Camera movement for a shot."""
    equipment: MovementEquipment = MovementEquipment.STATIC
    movement_type: MovementType = MovementType.STATIC
    timing: MovementTiming = MovementTiming.STATIC


class LightingConfig(BaseModel):
    """Lighting setup for a shot."""
    time_of_day: TimeOfDay = TimeOfDay.AFTERNOON
    source: LightingSource = LightingSource.SUN
    style: LightingStyle = LightingStyle.NATURALISTIC


class RenderingConfig(BaseModel):
    """Animation rendering style."""
    line_treatment: LineTreatment = LineTreatment.CLEAN
    color_application: ColorApplication = ColorApplication.CEL
    lighting_model: AnimLightingModel = AnimLightingModel.NATURALISTIC_SIMULATED
    surface_detail: SurfaceDetail = SurfaceDetail.SMOOTH


class MotionConfig(BaseModel):
    """Animation motion and virtual camera."""
    motion_style: MotionStyle = MotionStyle.FULL
    virtual_camera: VirtualCamera = VirtualCamera.DIGITAL_PAN


class LiveActionConfig(BaseModel):
    """Complete Live-Action cinema configuration."""
    camera: CameraConfig = Field(default_factory=CameraConfig)
    lens: LensConfig = Field(default_factory=LensConfig)
    movement: MovementConfig = Field(default_factory=MovementConfig)
    lighting: LightingConfig = Field(default_factory=LightingConfig)
    visual_grammar: VisualGrammar = Field(default_factory=VisualGrammar)
    film_preset: str | None = None
    era: str | None = None


class AnimationConfig(BaseModel):
    """Complete Animation configuration."""
    medium: AnimationMedium = AnimationMedium.TWO_D
    style_domain: StyleDomain = StyleDomain.ANIME
    rendering: RenderingConfig = Field(default_factory=RenderingConfig)
    motion: MotionConfig = Field(default_factory=MotionConfig)
    visual_grammar: VisualGrammar = Field(default_factory=VisualGrammar)
    style_preset: str | None = None
