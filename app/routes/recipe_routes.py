from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.controllers import RecipeController

recipe_bp = Blueprint("recipes", __name__)


@recipe_bp.route("/recipes", methods=["GET"])
def list_recipes():
    """List recipes with search, category filtering, and pagination."""
    return RecipeController.list()


@recipe_bp.route("/recipes/<int:recipe_id>", methods=["GET"])
def get_recipe(recipe_id):
    """Get one recipe."""
    return RecipeController.get(recipe_id)


@recipe_bp.route("/recipes", methods=["POST"])
@jwt_required()
def create_recipe():
    """Create a recipe (authenticated)."""
    return RecipeController.create()


@recipe_bp.route("/recipes/<int:recipe_id>", methods=["PUT"])
@jwt_required()
def update_recipe(recipe_id):
    """Update a recipe (authenticated)."""
    return RecipeController.update(recipe_id)


@recipe_bp.route("/recipes/<int:recipe_id>", methods=["DELETE"])
@jwt_required()
def delete_recipe(recipe_id):
    """Delete a recipe (authenticated)."""
    return RecipeController.delete(recipe_id)


@recipe_bp.route("/recipes/category/<string:category>", methods=["GET"])
def recipes_by_category(category):
    """List recipes in a category."""
    return RecipeController.by_category(category)
