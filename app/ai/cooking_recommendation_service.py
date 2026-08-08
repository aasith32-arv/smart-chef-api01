import json

from app.cooking_intelligence.cooking_validation_service import CookingValidationService
from app.services.ai_service import AIService


class CookingRecommendationService:
    SUBSTITUTIONS = {
        "yogurt": [
            {
                "substitution": "plain unsweetened dairy-free yogurt",
                "why_it_works": "It provides similar moisture and tang in marinades or sauces.",
                "how_much": "Start with the same measured amount.",
                "what_changes": "Flavour and thickness vary by product; avoid sweetened varieties.",
            }
        ],
        "coconut milk": [
            {
                "substitution": "unsweetened plant cream diluted to a pourable consistency",
                "why_it_works": "It can provide moisture and richness in a sauce.",
                "how_much": "Start 1:1, then adjust thickness gradually.",
                "what_changes": "The coconut aroma and final flavour will be different.",
            }
        ],
        "soy sauce": [
            {
                "substitution": "tamari",
                "why_it_works": "It supplies a similar salty fermented flavour.",
                "how_much": "Start with slightly less, taste, then add more if needed.",
                "what_changes": "Salt levels vary; check the label for dietary suitability.",
            }
        ],
        "oil": [
            {
                "substitution": "another neutral cooking oil suitable for the required heat",
                "why_it_works": "It provides a similar cooking medium and heat transfer.",
                "how_much": "Use the same amount initially.",
                "what_changes": "The aroma and heat tolerance depend on the chosen oil.",
            }
        ],
    }

    @classmethod
    def substitute(cls, ingredient, recipe_context="", use_ai=False):
        key = str(ingredient or "").strip().casefold()
        options = cls.SUBSTITUTIONS.get(key)
        if options:
            return {
                "ingredient": ingredient,
                "options": options,
                "context_warning": (
                    "Suitability depends on the recipe, allergies and dietary needs. "
                    "Use one option at a time and check labels."
                ),
                "source": "rule-based",
            }
        fallback = {
            "ingredient": ingredient,
            "options": [],
            "context_warning": (
                "No verified general substitution is stored for this ingredient. "
                "Do not replace it blindly; recipe context matters."
            ),
            "source": "rule-based-fallback",
        }
        if not use_ai or not AIService.is_configured():
            return fallback
        try:
            result = AIService._chat(
                (
                    "Suggest only context-appropriate cooking substitutions. Return JSON with "
                    "ingredient, options (array of substitution, why_it_works, how_much, "
                    "what_changes), and context_warning. Avoid unsafe allergy advice."
                ),
                json.dumps({"ingredient": ingredient, "recipe_context": recipe_context}),
                temperature=0.2,
            )
            if not CookingValidationService.validate_ai_payload(
                result, ("ingredient", "options", "context_warning")
            ):
                raise ValueError("Malformed AI substitution response")
            if not all(
                CookingValidationService.validate_ai_payload(
                    item, ("substitution", "why_it_works", "how_much", "what_changes")
                )
                for item in result["options"]
            ):
                raise ValueError("Malformed AI substitution option")
            return {**result, "source": AIService.provider()}
        except Exception:
            return fallback
