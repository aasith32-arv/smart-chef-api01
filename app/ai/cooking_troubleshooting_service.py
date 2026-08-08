import json

from app.cooking_intelligence.cooking_validation_service import CookingValidationService
from app.cooking_intelligence.troubleshooting_engine import TroubleshootingEngine
from app.services.ai_service import AIService


class CookingTroubleshootingService:
    REQUIRED = (
        "problem",
        "probable_cause",
        "immediate_action",
        "recovery_option",
        "prevention_tip",
    )

    @classmethod
    def troubleshoot(cls, problem, context="", use_ai=False):
        fallback = TroubleshootingEngine.solve(problem)
        if fallback:
            return fallback
        generic = {
            "problem": str(problem).strip(),
            "probable_cause": "The available recipe context is not enough to identify one cause.",
            "immediate_action": "Pause the heat if safe, inspect texture, moisture and aroma, then adjust gradually.",
            "recovery_option": "Use the nearest stored troubleshooting category or seek recipe-specific guidance.",
            "prevention_tip": "Check observable cues before each stage and make one small adjustment at a time.",
            "disclaimer": "The system cannot guarantee recovery; discard food if safety is uncertain.",
            "source": "rule-based-fallback",
        }
        if not use_ai or not AIService.is_configured():
            return generic
        try:
            result = AIService._chat(
                (
                    "Give conservative cooking troubleshooting. Return JSON with problem, "
                    "probable_cause, immediate_action, recovery_option, prevention_tip. Do not "
                    "guarantee recovery and do not override food-safety checks."
                ),
                json.dumps({"problem": problem, "context": context}),
                temperature=0.2,
            )
            if not CookingValidationService.validate_ai_payload(result, cls.REQUIRED):
                raise ValueError("Malformed AI troubleshooting response")
            return {
                **result,
                "disclaimer": "Recovery depends on severity; food-safety checks still apply.",
                "source": AIService.provider(),
            }
        except Exception:
            return generic
