from flask import request

from app.services import RecipeService, RecommendationService
from app.utils.responses import error_response, success_response
from app.validators import validate_recommend


class RecommendationController:
    @staticmethod
    def recommend():
        cleaned, errors = validate_recommend(request.get_json(silent=True))
        if errors:
            return error_response("Validation failed.", 400, errors)
        include_partial = request.args.get("partial", "true").lower() != "false"
        recommendations = RecommendationService.recommend(RecipeService.get_all_recipes(), cleaned["ingredients"], include_partial)
        if include_partial:
            recommendations = [item for item in recommendations if item["match_percentage"] > 0]
        return success_response({"available_ingredients": cleaned["ingredients"], "count": len(recommendations), "recommendations": recommendations}, "Recommendations generated successfully.")
