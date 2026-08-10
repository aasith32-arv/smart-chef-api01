from flask import request

from app.services import AIService, RecipeService, RecommendationService
from app.utils.responses import error_response, success_response


class AIController:
    @staticmethod
    def status():
        return success_response(AIService.status(), "AI status retrieved.")

    @staticmethod
    def plan():
        data = request.get_json(silent=True) or {}
        dish = (data.get("dish") or data.get("recipe") or "").strip()
        language = (data.get("language") or "en").strip() or "en"
        people = data.get("people")

        errors = {}
        if not dish:
            errors["dish"] = "dish is required and must be a non-empty string."
        try:
            people = int(people)
            if people < 1:
                errors["people"] = "people must be at least 1."
        except (TypeError, ValueError):
            errors["people"] = "people must be a positive integer."

        if errors:
            return error_response("Validation failed.", 400, errors)

        # Known recipes should be instant and deterministic. Calling a remote
        # provider first makes the calculator wait up to the provider timeout
        # even though the complete recipe already exists locally.
        recipe = RecipeService.get_by_name(dish)
        if recipe:
            try:
                plan = AIService.meal_plan_from_recipe(recipe, people, language)
            except ValueError as exc:
                return error_response(str(exc), 400)
            return success_response(plan, "Meal plan generated from local recipes.")

        if AIService.is_configured():
            try:
                plan = AIService.generate_meal_plan(dish, people, language)
                return success_response(
                    plan, f"Meal plan generated with {AIService.provider().title()}."
                )
            except Exception as exc:
                # Fall through to local recipe library
                local_error = str(exc)
        else:
            local_error = None

        message = f"Recipe '{dish}' not found."
        if local_error:
            message = f"{message} AI provider also failed: {local_error}"
        elif not AIService.is_configured():
            message = f"{message} Configure an AI provider for plans on unknown dishes."
        return error_response(message, 404)

    @staticmethod
    def suggest():
        data = request.get_json(silent=True) or {}
        ingredients = data.get("ingredients")
        language = (data.get("language") or "en").strip() or "en"

        if not isinstance(ingredients, list) or not ingredients:
            return error_response(
                "Validation failed.",
                400,
                {"ingredients": "ingredients is required and must be a non-empty list."},
            )
        cleaned = [str(item).strip() for item in ingredients if str(item).strip()]
        if not cleaned:
            return error_response(
                "Validation failed.",
                400,
                {"ingredients": "each ingredient must be a non-empty string."},
            )

        if AIService.is_configured():
            try:
                result = AIService.generate_suggestions(cleaned, language)
                return success_response(
                    result, f"Suggestions generated with {AIService.provider().title()}."
                )
            except Exception:
                # Prefer local matching when the selected provider is unavailable.
                pass

        recommendations = RecommendationService.recommend(
            RecipeService.get_all_recipes(), cleaned, include_partial=True
        )
        recommendations = [item for item in recommendations if item["match_percentage"] > 0]
        result = AIService.suggest_from_local(recommendations, cleaned)
        return success_response(result, "Suggestions generated from local recipes.")

    @staticmethod
    def translate():
        data = request.get_json(silent=True) or {}
        content = data.get("content")
        language = (data.get("language") or "en").strip() or "en"

        if not isinstance(content, dict):
            return error_response(
                "Validation failed.",
                400,
                {"content": "content is required and must be an object."},
            )

        try:
            translated = AIService.translate_content(content, language)
        except Exception as exc:
            return error_response(str(exc), 502)

        return success_response(translated, "Content translated.")
