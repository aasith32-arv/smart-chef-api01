from flask import request

from app.ai import (
    CookingExplanationService,
    CookingRecommendationService,
    CookingTroubleshootingService,
)
from app.cooking_intelligence import CookingPlanService, TroubleshootingEngine
from app.services import RecipeService
from app.utils.responses import error_response, success_response


class CookingController:
    @staticmethod
    def plan(recipe_id):
        recipe = RecipeService.get_by_id(recipe_id)
        if not recipe:
            return error_response("Recipe not found.", 404)
        payload = request.get_json(silent=True) if request.method == "POST" else request.args
        plan, errors = CookingPlanService.build(recipe, payload)
        if errors:
            return error_response("Cooking plan validation failed.", 400, errors)
        return success_response(plan, "Cooking intelligence plan generated.")

    @staticmethod
    def steps(recipe_id):
        recipe = RecipeService.get_by_id(recipe_id)
        if not recipe:
            return error_response("Recipe not found.", 404)
        plan, errors = CookingPlanService.build(recipe, request.args)
        if errors:
            return error_response("Cooking step validation failed.", 400, errors)
        return success_response(
            {"recipe_id": recipe.id, "steps": plan["steps"], "source": plan["source"]},
            "Cooking steps retrieved.",
        )

    @staticmethod
    def troubleshoot():
        data = request.get_json(silent=True) or {}
        problem = str(data.get("problem") or "").strip()
        if not problem:
            return error_response(
                "Validation failed.", 400, {"problem": "problem is required."}
            )
        result = CookingTroubleshootingService.troubleshoot(
            problem,
            str(data.get("context") or ""),
            bool(data.get("use_ai", False)),
        )
        result["supported_problems"] = TroubleshootingEngine.supported_problems()
        return success_response(result, "Troubleshooting guidance generated.")

    @staticmethod
    def substitute():
        data = request.get_json(silent=True) or {}
        ingredient = str(data.get("ingredient") or "").strip()
        if not ingredient:
            return error_response(
                "Validation failed.", 400, {"ingredient": "ingredient is required."}
            )
        context = str(data.get("recipe_context") or "")
        recipe_id = data.get("recipe_id")
        if recipe_id:
            try:
                recipe = RecipeService.get_by_id(int(recipe_id))
            except (TypeError, ValueError):
                return error_response(
                    "Validation failed.", 400, {"recipe_id": "recipe_id must be an integer."}
                )
            if not recipe:
                return error_response("Recipe not found.", 404)
            context = f"{recipe.name}: {recipe.description or ''}"
        result = CookingRecommendationService.substitute(
            ingredient, context, bool(data.get("use_ai", False))
        )
        return success_response(result, "Substitution guidance generated.")

    @staticmethod
    def explain():
        data = request.get_json(silent=True) or {}
        action = str(data.get("action") or "").strip()
        if not action:
            return error_response(
                "Validation failed.", 400, {"action": "action is required."}
            )
        result = CookingExplanationService.explain(
            action,
            str(data.get("context") or ""),
            bool(data.get("use_ai", False)),
        )
        return success_response(result, "Cooking explanation generated.")
