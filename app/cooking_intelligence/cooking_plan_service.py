from app.cooking_intelligence.cooking_sequence_engine import CookingSequenceEngine
from app.cooking_intelligence.cooking_validation_service import CookingValidationService
from app.cooking_intelligence.doneness_engine import DonenessEngine
from app.cooking_intelligence.personalization_engine import PersonalizationEngine
from app.cooking_intelligence.temperature_engine import TemperatureEngine
from app.cooking_intelligence.timing_engine import TimingEngine
from app.cooking_intelligence.transformation_engine import TransformationEngine


class CookingPlanService:
    """Build a validated cooking plan from curated steps or legacy recipe instructions."""

    PURPOSES = {
        "prepare": "Prepare ingredients so the active cooking stages run evenly.",
        "marinate": "Season the ingredient and allow flavours to coat it before cooking.",
        "preheat": "Create a controlled cooking surface before ingredients are added.",
        "saute": "Develop an aromatic flavour base with controlled browning.",
        "fry": "Cook and colour the surface while managing moisture.",
        "stir_fry": "Cook small pieces quickly while preserving texture.",
        "boil": "Use active moist heat to cook or hydrate the ingredient.",
        "simmer": "Cook gently so ingredients tenderize and flavours combine.",
        "dum": "Finish with gentle enclosed heat and retained steam.",
        "combine": "Distribute ingredients and seasoning evenly.",
        "rest": "Allow heat and moisture to redistribute before the next action.",
        "finish": "Complete the dish while preserving final texture and aroma.",
        "cook": "Advance the stored recipe method using observable cues.",
    }

    @classmethod
    def build(cls, recipe, payload=None):
        preferences, errors = PersonalizationEngine.normalize(payload, recipe.serving_size)
        if errors:
            return None, errors
        scaled = PersonalizationEngine.scaled_ingredients(recipe, preferences)
        scaled_by_id = {item["id"]: item for item in scaled}
        if recipe.cooking_steps:
            steps = [
                cls._stored_step(step, scaled_by_id, preferences)
                for step in recipe.cooking_steps
            ]
            plan_source = "stored"
        else:
            steps = [
                cls._rule_step(index, instruction, recipe, scaled_by_id, preferences)
                for index, instruction in enumerate(recipe.steps or [], start=1)
            ]
            plan_source = "rule-based"

        total_minutes = TimingEngine.timeline(steps)
        plan = {
            "recipe": {
                "id": recipe.id,
                "name": recipe.name,
                "category": recipe.category,
                "description": recipe.description,
                "base_servings": recipe.serving_size,
            },
            "servings": preferences["servings"],
            "ingredients": scaled,
            "steps": steps,
            "summary": {
                "estimated_minutes": total_minutes,
                "difficulty": cls._difficulty(steps),
                "heat_profile": cls._heat_profile(steps),
                "stages": len(steps),
                "ingredients": len(scaled),
                "critical_steps": sum(1 for step in steps if step["critical"]),
            },
            "personalization": preferences,
            "personalization_notes": PersonalizationEngine.notes(recipe, preferences, scaled),
            "source": plan_source,
            "estimate_notice": (
                "Timing, temperature and colour progress are practical estimates. Appearance "
                "varies with ingredients, lighting, cookware, stove and batch size. Manually "
                "confirm each stage before continuing."
            ),
            "safety_source": (
                "Food-temperature guidance follows USDA FSIS minimum internal-temperature "
                "recommendations for poultry and fish."
            ),
        }
        validation_errors = CookingValidationService.validate_plan(plan, recipe)
        if validation_errors:
            return None, {"plan": validation_errors}
        return plan, None

    @classmethod
    def _rule_step(cls, number, instruction, recipe, scaled_by_id, preferences):
        stage = CookingSequenceEngine.classify_stage(instruction)
        matched = CookingSequenceEngine.ingredients_for_step(instruction, recipe.ingredients)
        names = [ingredient.name for ingredient in matched]
        timing = TimingEngine.estimate(instruction, stage)
        temperature = TemperatureEngine.guidance(stage, names)
        doneness = DonenessEngine.cues(stage, instruction, names)
        transformation = TransformationEngine.describe(stage, names)
        additions = []
        for order, ingredient in enumerate(matched, start=1):
            scaled = scaled_by_id[ingredient.id]
            additions.append(
                {
                    **scaled,
                    "addition_order": order,
                    **CookingSequenceEngine.ingredient_guidance(ingredient, stage),
                }
            )
        warnings = cls._warnings(stage, temperature)
        return {
            "id": f"generated-{recipe.id}-{number}",
            "step_number": number,
            "title": CookingSequenceEngine.title_for(instruction, stage),
            "instruction": instruction,
            "beginner_instruction": PersonalizationEngine.beginner_instruction(
                temperature["heat_level"]
            ),
            "stage": stage,
            "timing": timing,
            "temperature": temperature,
            "ingredients": additions,
            "doneness": doneness,
            "transformation": transformation,
            "purpose": cls.PURPOSES.get(stage, cls.PURPOSES["cook"]),
            "benefits": cls._benefits(additions),
            "warnings": warnings,
            "common_mistakes": cls._mistakes(stage),
            "correction": cls._correction(stage),
            "scientific_explanation": transformation["science"],
            "critical": bool(temperature["food_safety"]) or stage in {"fry", "dum"},
            "source": "rule-based",
            "science_visible": preferences["science_mode"],
        }

    @classmethod
    def _stored_step(cls, step, scaled_by_id, preferences):
        data = step.to_dict()
        stage = CookingSequenceEngine.classify_stage(step.instruction)
        names = [item["name"] for item in data["ingredients"]]
        timing = {
            "minimum_minutes": step.minimum_duration or step.duration or 0,
            "maximum_minutes": step.maximum_duration or step.duration or 0,
            "estimated_minutes": step.duration
            or round(((step.minimum_duration or 0) + (step.maximum_duration or 0)) / 2),
            "source": "stored",
        }
        temperature = TemperatureEngine.guidance(stage, names)
        temperature.update(
            {
                "heat_level": step.heat_level or temperature["heat_level"],
                "minimum_c": step.temperature_min,
                "maximum_c": step.temperature_max,
            }
        )
        ingredients = []
        for addition in data["ingredients"]:
            scaled = scaled_by_id.get(addition["id"])
            if scaled:
                ingredients.append({**addition, **scaled})
        doneness = DonenessEngine.cues(stage, step.instruction, names)
        doneness.update(
            {
                "visual_cue": step.visual_cue or doneness["visual_cue"],
                "colour_stage": step.colour_stage or doneness["colour_stage"],
                "texture_cue": step.texture_cue or doneness["texture_cue"],
                "aroma_cue": step.aroma_cue or doneness["aroma_cue"],
            }
        )
        return {
            "id": step.id,
            "step_number": step.step_number,
            "title": step.title,
            "instruction": step.instruction,
            "beginner_instruction": PersonalizationEngine.beginner_instruction(
                temperature["heat_level"]
            ),
            "stage": stage,
            "timing": timing,
            "temperature": temperature,
            "ingredients": ingredients,
            "doneness": doneness,
            "transformation": data["transformation"],
            "purpose": step.purpose,
            "benefits": step.benefits or [],
            "warnings": step.warnings or [],
            "common_mistakes": step.common_mistakes or [],
            "correction": step.correction,
            "scientific_explanation": step.scientific_explanation,
            "critical": step.critical,
            "source": step.source,
            "science_visible": preferences["science_mode"],
        }

    @staticmethod
    def _benefits(additions):
        values = []
        for item in additions:
            for benefit in item["contribution"].split(","):
                clean = benefit.strip()
                if clean and clean not in values:
                    values.append(clean)
        return values[:5] or ["progresses the stored recipe method"]

    @staticmethod
    def _warnings(stage, temperature):
        warnings = []
        if stage in {"saute", "fry", "stir_fry"}:
            warnings.append("Reduce heat immediately if the food smokes or develops black patches.")
        if stage in {"simmer", "dum"}:
            warnings.append("Check that the pan does not cook dry or catch on the bottom.")
        if temperature["food_safety"]:
            warnings.append(temperature["food_safety"])
        return warnings

    @staticmethod
    def _mistakes(stage):
        if stage in {"saute", "fry", "stir_fry"}:
            return [
                {
                    "problem": "Heat too high",
                    "correction": "Lower the heat and move the food before it scorches.",
                }
            ]
        if stage in {"simmer", "boil", "dum"}:
            return [
                {
                    "problem": "Judging only by time",
                    "correction": "Check tenderness, bubbles and moisture before continuing.",
                }
            ]
        return [
            {
                "problem": "Skipping the observable cue",
                "correction": "Pause and verify the described appearance or texture.",
            }
        ]

    @staticmethod
    def _correction(stage):
        if stage in {"saute", "fry", "stir_fry"}:
            return "Move the pan off heat briefly, lower the flame, and continue only if unburnt."
        if stage in {"simmer", "boil", "dum"}:
            return "Adjust heat and moisture gradually, then reassess the densest ingredient."
        return "Pause, compare the observable cues, and adjust gradually before continuing."

    @staticmethod
    def _difficulty(steps):
        critical = sum(1 for step in steps if step["critical"])
        if len(steps) >= 8 or critical >= 3:
            return "Advanced"
        if len(steps) >= 6 or critical >= 1:
            return "Medium"
        return "Easy"

    @staticmethod
    def _heat_profile(steps):
        profile = []
        for step in steps:
            heat = step["temperature"]["heat_level"]
            if heat != "OFF" and (not profile or profile[-1] != heat):
                profile.append(heat)
        return " → ".join(profile) if profile else "No active heat"
