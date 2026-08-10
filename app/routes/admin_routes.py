from flask import Blueprint

from app.controllers.admin_controller import AdminController
from app.security import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/dashboard")
@admin_required
def admin_dashboard():
    return AdminController.dashboard()


@admin_bp.get("/recipes")
@admin_required
def admin_recipes():
    return AdminController.recipes()


@admin_bp.post("/recipes")
@admin_required
def admin_create_recipe():
    return AdminController.create_recipe()


@admin_bp.get("/recipes/<int:recipe_id>")
@admin_required
def admin_recipe(recipe_id):
    return AdminController.recipe(recipe_id)


@admin_bp.put("/recipes/<int:recipe_id>")
@admin_required
def admin_update_recipe(recipe_id):
    return AdminController.update_recipe(recipe_id)


@admin_bp.delete("/recipes/<int:recipe_id>")
@admin_required
def admin_delete_recipe(recipe_id):
    return AdminController.delete_recipe(recipe_id)


@admin_bp.post("/recipes/<int:recipe_id>/duplicate")
@admin_required
def admin_duplicate_recipe(recipe_id):
    return AdminController.duplicate_recipe(recipe_id)


@admin_bp.get("/dish-families")
@admin_required
def admin_families():
    return AdminController.families()


@admin_bp.post("/dish-families")
@admin_required
def admin_create_family():
    return AdminController.create_family()


@admin_bp.put("/dish-families/<int:family_id>")
@admin_required
def admin_update_family(family_id):
    return AdminController.update_family(family_id)


@admin_bp.delete("/dish-families/<int:family_id>")
@admin_required
def admin_delete_family(family_id):
    return AdminController.delete_family(family_id)


@admin_bp.get("/categories")
@admin_required
def admin_categories():
    return AdminController.categories()


@admin_bp.patch("/categories")
@admin_required
def admin_rename_category():
    return AdminController.rename_category()


@admin_bp.get("/users")
@admin_required
def admin_users():
    return AdminController.users()


@admin_bp.patch("/users/<int:user_id>")
@admin_required
def admin_update_user(user_id):
    return AdminController.update_user(user_id)


@admin_bp.get("/advertisements")
@admin_required
def admin_advertisements():
    return AdminController.advertisements()


@admin_bp.patch("/advertisements/<int:order_id>")
@admin_required
def admin_moderate_advertisement(order_id):
    return AdminController.moderate_advertisement(order_id)


@admin_bp.get("/payments")
@admin_required
def admin_payments():
    return AdminController.payments()


@admin_bp.get("/settings")
@admin_required
def admin_settings():
    return AdminController.settings()
