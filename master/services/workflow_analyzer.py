from typing import Dict, Any, List
from ..models.shot import Shot, WorkflowType


class WorkflowAnalyzer:
    """
    Rule-based workflow recommendation engine.
    Future: Integrate LLM for smarter analysis.
    """
    
    # Keyword constants for maintainability
    HIGH_MOTION_KEYWORDS: List[str] = ["run", "fly", "jump", "explode", "fight", "chase", "spin", "crash", "fall"]
    SUBTLE_MOTION_KEYWORDS: List[str] = ["blink", "breathing", "wind", "slow", "pan", "tilt", "drift", "float"]
    STYLIZED_KEYWORDS: List[str] = ["anime", "cartoon", "cel-shaded", "illustration", "2d"]
    
    def analyze_shot(self, shot: Shot) -> Dict[str, Any]:
        """
        Analyzes the shot description/action and recommends a workflow and prompt.
        """
        description = (shot.scene_description or "").lower()
        action = (shot.action or "").lower()
        text = f"{description} {action}"
        
        recommendation = {
            "recommended_workflow": WorkflowType.TEXT_TO_IMAGE,
            "reasoning": "Standard static shot.",
            "enhanced_prompt": shot.scene_description
        }
        
        # Rule 1: High motion -> Wan Animate
        if any(w in text for w in self.HIGH_MOTION_KEYWORDS):
            recommendation["recommended_workflow"] = WorkflowType.WAN_ANIMATE
            recommendation["reasoning"] = "Detected high-motion keywords. Video generation recommended."
            
        # Rule 2: Subtle motion -> SVI
        elif any(w in text for w in self.SUBTLE_MOTION_KEYWORDS):
            recommendation["recommended_workflow"] = WorkflowType.SVI
            recommendation["reasoning"] = "Subtle motion detected. SVI (Stable Video) is efficient."
            
        # Rule 3: Stylized content -> LTX-2
        elif any(w in text for w in self.STYLIZED_KEYWORDS):
            recommendation["recommended_workflow"] = WorkflowType.LTX2
            recommendation["reasoning"] = "Stylized content works well with LTX-2."

        return recommendation

