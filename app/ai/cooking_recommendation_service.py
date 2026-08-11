import json

from app.cooking_intelligence.cooking_validation_service import CookingValidationService
from app.services.ai_service import AIService


class CookingRecommendationService:
    """Conservative substitutions shared by Calculate and Guided Cooking."""

    CONTEXT_WARNING = (
        "Suitability depends on the recipe, dietary needs and product labels. "
        "Use one option at a time and monitor the stated cooking cues."
    )

    SUBSTITUTIONS = {
        "yogurt": [
            {
                "substitution": "plain unsweetened dairy-free yogurt",
                "suitability": "Good Alternative",
                "why_it_works": "It provides similar moisture and tang in marinades or sauces.",
                "how_much": "Start with the same measured amount.",
                "adjustment": "Choose a thick, unsweetened product and stir it smooth before use.",
                "what_changes": "Flavour and thickness vary by product; avoid sweetened varieties.",
            },
            {
                "substitution": "plain Greek yogurt diluted with water",
                "suitability": "Possible Alternative",
                "why_it_works": "It keeps the cultured tang and tenderising action of yogurt.",
                "how_much": "Thin gradually until it matches the original yogurt consistency.",
                "adjustment": "Whisk before adding so the thicker yogurt disperses evenly.",
                "what_changes": "The sauce or marinade may remain slightly thicker.",
            },
        ],
        "coconut milk": [
            {
                "substitution": "coconut cream diluted with water",
                "suitability": "Best Match",
                "why_it_works": "It preserves coconut flavour while restoring a milk-like consistency.",
                "how_much": "Use three parts coconut cream and one part water, keeping the same total amount.",
                "adjustment": "Whisk the cream and water together before adding.",
                "what_changes": "The result may be slightly richer depending on the cream.",
            },
            {
                "substitution": "unsweetened plant cream diluted to a pourable consistency",
                "suitability": "Possible Alternative",
                "why_it_works": "It can provide moisture and richness in a sauce.",
                "how_much": "Start 1:1, then adjust thickness gradually.",
                "adjustment": "Add gradually and stop when the sauce reaches the intended body.",
                "what_changes": "The coconut aroma and final flavour will be different.",
            },
        ],
        "soy sauce": [
            {
                "substitution": "tamari",
                "suitability": "Best Match",
                "why_it_works": "It supplies a similar salty fermented flavour.",
                "how_much": "Start with slightly less, taste, then add more if needed.",
                "adjustment": "Reduce other salt until the final seasoning is checked.",
                "what_changes": "Salt levels vary; check the label for dietary suitability.",
            }
        ],
        "oil": [
            {
                "substitution": "another neutral cooking oil suitable for the required heat",
                "suitability": "Good Alternative",
                "why_it_works": "It provides a similar cooking medium and heat transfer.",
                "how_much": "Use the same amount initially.",
                "adjustment": "Confirm the replacement oil is suitable for the cooking temperature.",
                "what_changes": "The aroma and heat tolerance depend on the chosen oil.",
            }
        ],
        "chicken": [
            {
                "substitution": "boneless turkey thigh",
                "suitability": "Best Match",
                "why_it_works": "Turkey thigh has a similar firm texture and stays moist during layered cooking.",
                "how_much": "Use the same measured weight.",
                "adjustment": "Cut it into matching pieces and cook until safely done; timing may be slightly longer.",
                "what_changes": "The flavour is a little stronger and the meat may be firmer.",
            },
            {
                "substitution": "firm paneer",
                "suitability": "Possible Alternative",
                "why_it_works": "Paneer holds its shape through marinating, layering and gentle dum cooking.",
                "how_much": "Use the same measured weight.",
                "adjustment": "Marinate briefly and add after the masala is cooked because paneer needs less cooking time.",
                "what_changes": "The dish becomes vegetarian, milder and less savoury than chicken biryani.",
            },
        ],
        "onion": [
            {
                "substitution": "shallots",
                "suitability": "Best Match",
                "why_it_works": "Shallots caramelise and provide the sweet allium base needed in the masala.",
                "how_much": "Use the same measured weight.",
                "adjustment": "Slice thinly and watch closely because shallots can brown faster.",
                "what_changes": "The flavour is slightly sweeter and more delicate.",
            },
            {
                "substitution": "leek, white part only",
                "suitability": "Possible Alternative",
                "why_it_works": "Leek supplies a mild allium flavour and softens into the sauce.",
                "how_much": "Use the same measured weight.",
                "adjustment": "Slice finely and cook until fully soft before adding spices.",
                "what_changes": "The masala will be milder and less caramelised.",
            },
        ],
        "ginger garlic paste": [
            {
                "substitution": "fresh grated ginger and garlic",
                "suitability": "Best Match",
                "why_it_works": "Fresh ginger and garlic provide the same aromatic foundation without premade paste.",
                "how_much": "Replace with equal parts ginger and garlic totalling the original amount.",
                "adjustment": "Grate or crush very finely and cook until the raw aroma disappears.",
                "what_changes": "The aroma may be fresher and sharper.",
            }
        ],
        "ghee": [
            {
                "substitution": "unsalted butter with neutral oil",
                "suitability": "Best Match",
                "why_it_works": "Butter provides richness while neutral oil raises heat tolerance.",
                "how_much": "Use three parts butter and one part neutral oil, keeping the same total amount.",
                "adjustment": "Use moderate heat so the butter solids do not burn.",
                "what_changes": "The aroma is buttery but lacks ghee's toasted nuttiness.",
            },
            {
                "substitution": "neutral cooking oil",
                "suitability": "Good Alternative",
                "why_it_works": "It supplies the fat needed to fry aromatics and keep rice grains separate.",
                "how_much": "Use slightly less than the original amount, then add only if needed.",
                "adjustment": "Choose an oil suitable for the cooking temperature.",
                "what_changes": "The dish will be lighter and will not have ghee aroma.",
            },
        ],
        "mint leaves": [
            {
                "substitution": "fresh coriander leaves with a little lime zest",
                "suitability": "Good Alternative",
                "why_it_works": "Fresh coriander and lime zest restore herbal freshness and a cooling citrus lift.",
                "how_much": "Use the same herb amount and add lime zest sparingly.",
                "adjustment": "Add most of it during layering and reserve a little for finishing.",
                "what_changes": "The characteristic cool mint aroma will be replaced by citrus-herb notes.",
            }
        ],
        "coriander leaves": [
            {
                "substitution": "flat-leaf parsley",
                "suitability": "Good Alternative",
                "why_it_works": "Parsley supplies fresh green flavour and colour without dominating the masala.",
                "how_much": "Use the same measured amount.",
                "adjustment": "Add near the end or during layering to preserve freshness.",
                "what_changes": "The result is milder and lacks coriander's citrus character.",
            }
        ],
        "salt": [
            {
                "substitution": "fine sea salt",
                "suitability": "Best Match",
                "why_it_works": "Fine sea salt seasons the dish in the same way as ordinary cooking salt.",
                "how_much": "Start with three quarters of the amount, taste, then adjust.",
                "adjustment": "Account for different crystal sizes and any salt already present in spice blends.",
                "what_changes": "There should be little flavour change once seasoning is balanced.",
            }
        ],
        "biryani masala": [
            {
                "substitution": "garam masala with ground cumin and coriander",
                "suitability": "Good Alternative",
                "why_it_works": "The blend restores the warm, earthy spice profile of biryani masala.",
                "how_much": "Use two parts garam masala, one part cumin and one part coriander to make the same total amount.",
                "adjustment": "Add chilli separately to match the intended heat and bloom the spices briefly in fat.",
                "what_changes": "The aroma will be less specialised and may lack floral notes.",
            }
        ],
        "lemon juice": [
            {
                "substitution": "lime juice",
                "suitability": "Best Match",
                "why_it_works": "Lime supplies comparable acidity and fresh citrus aroma.",
                "how_much": "Start with slightly less, taste, then increase if needed.",
                "adjustment": "Add gradually because lime can taste sharper than lemon.",
                "what_changes": "The citrus note will be sharper and more floral.",
            },
            {
                "substitution": "mild white vinegar diluted with water",
                "suitability": "Possible Alternative",
                "why_it_works": "Diluted vinegar restores acidity when fresh citrus is unavailable.",
                "how_much": "Use equal parts vinegar and water, then add gradually to taste.",
                "adjustment": "Add less than the original amount first and stop when the masala tastes balanced.",
                "what_changes": "It adds acidity without fresh citrus aroma.",
            },
        ],
        "saffron milk": [
            {
                "substitution": "warm milk with turmeric and cardamom",
                "suitability": "Good Alternative",
                "why_it_works": "It supplies moisture, golden colour and a complementary floral spice note.",
                "how_much": "Use the same milk amount with only a small pinch of turmeric.",
                "adjustment": "Steep the cardamom in warm milk and use turmeric sparingly to avoid an earthy taste.",
                "what_changes": "The rice will be golden but will not have saffron's distinctive aroma.",
            }
        ],
    }

    BIRYANI_RICE = [
        {
            "substitution": "sella basmati rice",
            "suitability": "Best Match",
            "why_it_works": "It is a firm long-grain basmati that stays separate during layering and dum cooking.",
            "how_much": "Use the same measured amount.",
            "adjustment": "Soak according to the packet and check the parboil stage before layering.",
            "what_changes": "The grains are firmer and may need a little more cooking time.",
        },
        {
            "substitution": "jeerakasala rice",
            "suitability": "Good Alternative",
            "why_it_works": "This aromatic rice is traditionally used in South Indian layered biryanis.",
            "how_much": "Use the same measured amount.",
            "adjustment": "Reduce soaking and begin checking doneness earlier than for basmati.",
            "what_changes": "The grain is shorter, with a more compact texture and different aroma.",
        },
        {
            "substitution": "seeraga samba rice",
            "suitability": "Possible Alternative",
            "why_it_works": "Its aromatic short grain absorbs masala well in Tamil-style biryani methods.",
            "how_much": "Use the same measured amount.",
            "adjustment": "Use the water and timing cues for seeraga samba rather than basmati.",
            "what_changes": "The result is more compact and masala-forward than long-grain biryani.",
        },
    ]

    FRIED_RICE = [
        {
            "substitution": "jasmine rice",
            "suitability": "Good Alternative",
            "why_it_works": "Cooked jasmine rice can remain distinct enough for high-heat stir-frying.",
            "how_much": "Use the same measured amount of cooked rice.",
            "adjustment": "Cook with slightly less water, cool fully, and chill before frying.",
            "what_changes": "The grains are softer and more aromatic than standard long-grain rice.",
        },
        {
            "substitution": "long-grain rice",
            "suitability": "Possible Alternative",
            "why_it_works": "Dry, separate long grains withstand tossing better than sticky rice.",
            "how_much": "Use the same measured amount of cooked rice.",
            "adjustment": "Cool completely before frying to prevent clumping.",
            "what_changes": "Aroma and grain firmness depend on the variety.",
        },
    ]

    @staticmethod
    def _normalized_key(ingredient):
        key = " ".join(str(ingredient or "").strip().casefold().split())
        if key == "curd":
            return "yogurt"
        if key.endswith(" oil") or key in {"cooking oil", "vegetable oil"}:
            return "oil"
        return key

    @classmethod
    def _contextual_options(cls, ingredient, recipe):
        key = cls._normalized_key(ingredient)
        family = recipe.family.slug.casefold() if recipe and recipe.family else ""
        recipe_name = recipe.name.casefold() if recipe else ""

        if "rice" in key and (family == "biryani" or "biryani" in recipe_name):
            return cls.BIRYANI_RICE
        if "rice" in key and (family == "fried-rice" or "fried rice" in recipe_name):
            return cls.FRIED_RICE
        return cls.SUBSTITUTIONS.get(key)

    @classmethod
    def substitute(
        cls,
        ingredient,
        recipe_context="",
        use_ai=False,
        *,
        recipe=None,
        original_quantity=None,
        original_unit=None,
        original_display=None,
    ):
        options = cls._contextual_options(ingredient, recipe)
        if options:
            enriched_options = [
                {
                    **option,
                    "quantity": original_quantity,
                    "unit": original_unit,
                    "display_quantity": original_display,
                }
                for option in options
            ]
            return {
                "ingredient": ingredient,
                "original_quantity": original_quantity,
                "original_unit": original_unit,
                "original_display": original_display,
                "recipe_id": recipe.id if recipe else None,
                "options": enriched_options,
                "no_substitute_reason": None,
                "context_warning": cls.CONTEXT_WARNING,
                "source": "contextual-rule-based" if recipe else "rule-based",
            }

        no_substitute_reason = (
            "This ingredient has an important role in this recipe, and AI Chef does not "
            "have a reliable context-specific replacement for it."
        )
        fallback = {
            "ingredient": ingredient,
            "original_quantity": original_quantity,
            "original_unit": original_unit,
            "original_display": original_display,
            "recipe_id": recipe.id if recipe else None,
            "options": [],
            "no_substitute_reason": no_substitute_reason,
            "context_warning": no_substitute_reason,
            "source": "rule-based-fallback",
        }
        # A known stored recipe must never bypass the deterministic safety decision.
        if recipe or not use_ai or not AIService.is_configured():
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
