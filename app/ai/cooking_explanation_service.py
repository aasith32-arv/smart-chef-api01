import json

from app.cooking_intelligence.cooking_validation_service import CookingValidationService
from app.services.ai_service import AIService


class CookingExplanationService:
    EXPLANATIONS = {
        "whole spices": (
            "Whole spices are often added to warm fat so their aromas can spread before wetter "
            "ingredients lower the pan temperature."
        ),
        "onion": (
            "Onion needs time to soften and possibly brown, building sweetness, colour and body."
        ),
        "spices": (
            "Adding ground spices to a moist flavour base helps them distribute while limiting "
            "prolonged exposure to dry high heat."
        ),
        "herbs": (
            "Delicate herbs are often added late so more of their fresh aroma and colour remain."
        ),
        "rest": (
            "Resting lets heat and moisture redistribute, which can improve consistency and texture."
        ),
    }

    @classmethod
    def explain(cls, action, context="", use_ai=False):
        key = str(action or "").strip().casefold()
        if not key:
            return None
        fallback = next(
            (text for name, text in cls.EXPLANATIONS.items() if name in key),
            (
                "This action belongs here because it follows the stored recipe dependencies and "
                "prepares the food for the next stage."
            ),
        )
        if not use_ai or not AIService.is_configured():
            return {"action": action, "explanation": fallback, "source": "rule-based"}

        prompt = {
            "action": action,
            "context": context,
            "fallback": fallback,
        }
        try:
            result = AIService._chat(
                (
                    "Explain a cooking action in one or two beginner-friendly sentences. "
                    "Return JSON with action and explanation. Avoid guarantees and do not invent "
                    "quantities, temperatures or recipe facts."
                ),
                json.dumps(prompt),
                temperature=0.2,
            )
            if not CookingValidationService.validate_ai_payload(
                result, ("action", "explanation")
            ):
                raise ValueError("Malformed AI explanation")
            return {**result, "source": AIService.provider()}
        except Exception:
            return {"action": action, "explanation": fallback, "source": "rule-based-fallback"}
