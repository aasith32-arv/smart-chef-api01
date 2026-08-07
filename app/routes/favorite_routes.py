from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.controllers import FavoriteController

favorite_bp = Blueprint("favorites", __name__)


@favorite_bp.route("/favorites", methods=["GET"])
@jwt_required()
def list_favorites():
    """List the authenticated user's favorites."""
    return FavoriteController.list()


@favorite_bp.route("/favorites", methods=["POST"])
@jwt_required()
def add_favorite():
    """Add a recipe to the authenticated user's favorites."""
    return FavoriteController.create()


@favorite_bp.route("/favorites/<int:recipe_id>", methods=["DELETE"])
@jwt_required()
def remove_favorite(recipe_id):
    """Remove a recipe from the authenticated user's favorites."""
    return FavoriteController.delete(recipe_id)
