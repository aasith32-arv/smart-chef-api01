from flask import current_app, request

from app.services import DishFamilyService, RecipeService
from app.utils.responses import error_response, success_response


class DishFamilyController:
    @staticmethod
    def list():
        families = DishFamilyService.get_all(
            category=request.args.get("category"),
            search=request.args.get("search"),
        )
        return success_response(
            {"items": families, "count": len(families)},
            "Dish families retrieved successfully.",
        )

    @staticmethod
    def get(slug):
        family = DishFamilyService.get_by_slug(slug)
        if not family:
            return error_response("Dish family not found.", 404)
        return success_response(
            {"family": family.to_dict()}, "Dish family retrieved successfully."
        )

    @staticmethod
    def recipes(slug):
        family = DishFamilyService.get_by_slug(slug)
        if not family:
            return error_response("Dish family not found.", 404)

        page = max(request.args.get("page", 1, type=int) or 1, 1)
        default_size = current_app.config["DEFAULT_PAGE_SIZE"]
        per_page = request.args.get("per_page", default_size, type=int) or default_size
        per_page = min(max(per_page, 1), current_app.config["MAX_PAGE_SIZE"])
        recipes = RecipeService.get_all(
            page=page,
            per_page=per_page,
            search=request.args.get("search"),
            family=family.slug,
            cuisine=request.args.get("cuisine"),
            region=request.args.get("region"),
            protein=request.args.get("protein"),
            diet_type=request.args.get("diet_type"),
            difficulty=request.args.get("difficulty"),
            spice_level=request.args.get("spice_level"),
            max_cook_time=request.args.get("max_cook_time", type=int),
        )
        recipes["family"] = family.to_dict()
        return success_response(recipes, "Recipe varieties retrieved successfully.")
