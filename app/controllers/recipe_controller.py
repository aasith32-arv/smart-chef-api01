from flask import current_app, request

from app.services import RecipeService
from app.utils.responses import error_response, success_response
from app.validators import validate_recipe_create, validate_recipe_update


class RecipeController:
    @staticmethod
    def _pagination_params():
        page = max(request.args.get("page", 1, type=int) or 1, 1)
        default_size = current_app.config["DEFAULT_PAGE_SIZE"]
        per_page = request.args.get("per_page", default_size, type=int) or default_size
        per_page = min(max(per_page, 1), current_app.config["MAX_PAGE_SIZE"])
        return page, per_page

    @classmethod
    def list(cls):
        page, per_page = cls._pagination_params()
        result = RecipeService.get_all(page, per_page, request.args.get("search"), request.args.get("category"))
        return success_response(result, "Recipes retrieved successfully.")

    @staticmethod
    def get(recipe_id):
        recipe = RecipeService.get_by_id(recipe_id)
        if not recipe:
            return error_response("Recipe not found.", 404)
        return success_response({"recipe": recipe.to_dict()}, "Recipe retrieved successfully.")

    @staticmethod
    def create():
        cleaned, errors = validate_recipe_create(request.get_json(silent=True))
        if errors:
            return error_response("Validation failed.", 400, errors)
        recipe, message, status = RecipeService.create(cleaned)
        if not recipe:
            return error_response(message, status)
        return success_response({"recipe": recipe.to_dict()}, "Recipe created successfully.", status)

    @staticmethod
    def update(recipe_id):
        recipe = RecipeService.get_by_id(recipe_id)
        if not recipe:
            return error_response("Recipe not found.", 404)
        cleaned, errors = validate_recipe_update(request.get_json(silent=True))
        if errors:
            return error_response("Validation failed.", 400, errors)
        recipe, message, status = RecipeService.update(recipe, cleaned)
        if not recipe:
            return error_response(message, status)
        return success_response({"recipe": recipe.to_dict()}, "Recipe updated successfully.", status)

    @staticmethod
    def delete(recipe_id):
        recipe = RecipeService.get_by_id(recipe_id)
        if not recipe:
            return error_response("Recipe not found.", 404)
        RecipeService.delete(recipe)
        return success_response(message="Recipe deleted successfully.")

    @classmethod
    def by_category(cls, category):
        page, per_page = cls._pagination_params()
        result = RecipeService.get_by_category(category, page, per_page)
        return success_response(result, f"Recipes in category '{category}' retrieved successfully.")
