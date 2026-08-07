from flask import Blueprint

from app.controllers import RecommendationController

recommendation_bp = Blueprint("recommendation", __name__)


@recommendation_bp.route("/recommend", methods=["POST"])
def recommend_recipes():
    """Recommend recipes from available ingredients."""
    return RecommendationController.recommend()
