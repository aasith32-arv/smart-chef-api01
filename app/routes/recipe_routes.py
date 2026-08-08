from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.controllers import CookingController, RecipeController

recipe_bp = Blueprint("recipes", __name__)


@recipe_bp.route("/recipes", methods=["GET"])
def list_recipes():
    """List recipes with search, category filtering, and pagination."""
    return RecipeController.list()


@recipe_bp.route("/recipes/<int:recipe_id>", methods=["GET"])
def get_recipe(recipe_id):
    """Get one recipe."""
    return RecipeController.get(recipe_id)


@recipe_bp.route("/recipes/<int:recipe_id>/cooking-plan", methods=["GET", "POST"])
def cooking_plan(recipe_id):
    """Generate a structured, personalized cooking intelligence plan.
    ---
    tags: [Cooking Intelligence]
    parameters:
      - in: path
        name: recipe_id
        required: true
        type: integer
      - in: body
        name: preferences
        required: false
        schema:
          type: object
          properties:
            servings: {type: integer, minimum: 1, maximum: 100}
            spice_level: {type: string, enum: [mild, medium, hot]}
            oil_level: {type: string, enum: [low, standard]}
            salt_preference: {type: string, enum: [low, standard]}
            dietary_restrictions: {type: array, items: {type: string}}
            cookware: {type: string}
            preferred_texture: {type: string}
            beginner_mode: {type: boolean}
            science_mode: {type: boolean}
    responses:
      200: {description: Validated cooking plan}
      400: {description: Invalid personalization or plan data}
      404: {description: Recipe not found}
    """
    return CookingController.plan(recipe_id)


@recipe_bp.route("/recipes/<int:recipe_id>/cooking-steps", methods=["GET"])
def cooking_steps(recipe_id):
    """Return structured cooking steps for a recipe.
    ---
    tags: [Cooking Intelligence]
    parameters:
      - in: path
        name: recipe_id
        required: true
        type: integer
    responses:
      200: {description: Structured cooking steps}
      404: {description: Recipe not found}
    """
    return CookingController.steps(recipe_id)


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
