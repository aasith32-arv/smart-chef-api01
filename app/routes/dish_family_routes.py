from flask import Blueprint

from app.controllers import DishFamilyController

dish_family_bp = Blueprint("dish_families", __name__)


@dish_family_bp.route("/dish-families", methods=["GET"])
def list_dish_families():
    """List active dish families, optionally filtered by category or search."""
    return DishFamilyController.list()


@dish_family_bp.route("/dish-families/<string:slug>", methods=["GET"])
def get_dish_family(slug):
    """Get one active dish family by stable slug."""
    return DishFamilyController.get(slug)


@dish_family_bp.route("/dish-families/<string:slug>/recipes", methods=["GET"])
def list_dish_family_recipes(slug):
    """List paginated recipe varieties for a dish family."""
    return DishFamilyController.recipes(slug)
