from flask import request

from app.services import QuantityCalculatorService, RecipeService
from app.utils.responses import error_response, success_response
from app.validators import validate_calculate


class CalculatorController:
    @staticmethod
    def calculate():
        cleaned, errors = validate_calculate(request.get_json(silent=True))
        if errors:
            return error_response("Validation failed.", 400, errors)
        recipe = RecipeService.get_by_name(cleaned["recipe"])
        if not recipe:
            return error_response(f"Recipe '{cleaned['recipe']}' not found.", 404)
        quantities, error = QuantityCalculatorService.calculate_for_recipe(recipe, cleaned["people"])
        if error:
            return error_response(error, 400)
        return success_response({"recipe": recipe.name, "people": cleaned["people"], "serving_size": recipe.serving_size, "quantities": quantities}, "Quantities calculated successfully.")
