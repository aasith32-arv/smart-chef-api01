from flask import g, request

from app.extensions import db
from app.models import AdvertisingOrder, DishFamily, Recipe, User
from app.services import AdminService
from app.utils import slugify
from app.utils.responses import error_response, success_response
from app.validators import (
    validate_admin_family,
    validate_admin_recipe,
    validate_admin_user_update,
)
from app.validators.admin_validator import ADVERTISEMENT_REVIEW_STATUSES


class AdminController:
    @staticmethod
    def _pagination():
        page = max(request.args.get("page", 1, type=int) or 1, 1)
        default_size = 20
        maximum = 100
        per_page = request.args.get("per_page", default_size, type=int) or default_size
        return page, min(max(per_page, 1), maximum)

    @staticmethod
    def dashboard():
        return success_response(AdminService.dashboard(), "Admin dashboard retrieved.")

    @classmethod
    def recipes(cls):
        page, per_page = cls._pagination()
        data = AdminService.recipes(
            page=page,
            per_page=per_page,
            search=request.args.get("search"),
            category=request.args.get("category"),
            family=request.args.get("family"),
            cuisine=request.args.get("cuisine"),
            region=request.args.get("region"),
            protein=request.args.get("protein"),
            diet_type=request.args.get("diet_type"),
            difficulty=request.args.get("difficulty"),
            spice_level=request.args.get("spice_level"),
            max_cook_time=request.args.get("max_cook_time", type=int),
            publication_status=request.args.get("status"),
        )
        return success_response(data, "Admin recipes retrieved.")

    @staticmethod
    def recipe(recipe_id):
        recipe = AdminService.recipe(recipe_id)
        if not recipe:
            return error_response("Recipe not found.", 404)
        return success_response({"recipe": recipe}, "Admin recipe retrieved.")

    @staticmethod
    def create_recipe():
        cleaned, errors = validate_admin_recipe(request.get_json(silent=True))
        if errors:
            return error_response("Validation failed.", 400, errors)
        recipe, message, status = AdminService.create_recipe(cleaned, g.admin_user.id)
        if not recipe:
            return error_response(message, status)
        return success_response(
            {"recipe": AdminService.recipe(recipe.id)},
            "Recipe created successfully.",
            201,
        )

    @staticmethod
    def update_recipe(recipe_id):
        recipe = db.session.get(Recipe, recipe_id)
        if not recipe:
            return error_response("Recipe not found.", 404)
        cleaned, errors = validate_admin_recipe(
            request.get_json(silent=True), partial=True
        )
        if errors:
            return error_response("Validation failed.", 400, errors)
        recipe, message, status = AdminService.update_recipe(
            recipe, cleaned, g.admin_user.id
        )
        if not recipe:
            return error_response(message, status)
        return success_response(
            {"recipe": AdminService.recipe(recipe.id)},
            "Recipe updated successfully.",
        )

    @staticmethod
    def duplicate_recipe(recipe_id):
        recipe = db.session.get(Recipe, recipe_id)
        if not recipe:
            return error_response("Recipe not found.", 404)
        copy, message, status = AdminService.duplicate_recipe(recipe, g.admin_user.id)
        if not copy:
            return error_response(message, status)
        return success_response(
            {"recipe": AdminService.recipe(copy.id)},
            "Recipe duplicated as a draft.",
            201,
        )

    @staticmethod
    def delete_recipe(recipe_id):
        recipe = db.session.get(Recipe, recipe_id)
        if not recipe:
            return error_response("Recipe not found.", 404)
        AdminService.deactivate_recipe(recipe, g.admin_user.id)
        return success_response(
            {"recipe": AdminService.recipe(recipe.id)},
            "Recipe deactivated successfully.",
        )

    @classmethod
    def families(cls):
        page, per_page = cls._pagination()
        return success_response(
            AdminService.families(
                search=request.args.get("search"), page=page, per_page=per_page
            ),
            "Admin dish families retrieved.",
        )

    @staticmethod
    def create_family():
        payload = request.get_json(silent=True) or {}
        if payload.get("name") and not payload.get("slug"):
            payload["slug"] = slugify(payload["name"])
        cleaned, errors = validate_admin_family(payload)
        if errors:
            return error_response("Validation failed.", 400, errors)
        family, message, status = AdminService.create_family(
            cleaned, g.admin_user.id
        )
        if not family:
            return error_response(message, status)
        return success_response(
            {"family": family.to_dict()}, "Dish family created successfully.", 201
        )

    @staticmethod
    def update_family(family_id):
        family = db.session.get(DishFamily, family_id)
        if not family:
            return error_response("Dish family not found.", 404)
        payload = request.get_json(silent=True) or {}
        cleaned, errors = validate_admin_family(payload, partial=True)
        if errors:
            return error_response("Validation failed.", 400, errors)
        family, message, status = AdminService.update_family(
            family, cleaned, g.admin_user.id
        )
        if not family:
            return error_response(message, status)
        return success_response(
            {"family": family.to_dict()}, "Dish family updated successfully."
        )

    @staticmethod
    def delete_family(family_id):
        family = db.session.get(DishFamily, family_id)
        if not family:
            return error_response("Dish family not found.", 404)
        deleted, message, status = AdminService.delete_family(
            family, g.admin_user.id
        )
        if not deleted:
            return error_response(message, status)
        return success_response(message="Dish family deleted successfully.")

    @staticmethod
    def categories():
        return success_response(
            {"items": AdminService.categories()}, "Admin categories retrieved."
        )

    @staticmethod
    def rename_category():
        data = request.get_json(silent=True) or {}
        old_name = str(data.get("old_name") or "").strip()
        new_name = " ".join(str(data.get("new_name") or "").strip().split())
        errors = {}
        if not old_name:
            errors["old_name"] = "old_name is required."
        if not new_name:
            errors["new_name"] = "new_name is required."
        elif len(new_name) > 80:
            errors["new_name"] = "new_name must not exceed 80 characters."
        if errors:
            return error_response("Validation failed.", 400, errors)
        result = AdminService.rename_category(old_name, new_name, g.admin_user.id)
        if not result:
            return error_response("Category not found.", 404)
        return success_response(result, "Category renamed successfully.")

    @classmethod
    def users(cls):
        page, per_page = cls._pagination()
        active = request.args.get("is_active")
        is_active = None if active is None else active.lower() in {"true", "1", "yes"}
        return success_response(
            AdminService.users(
                search=request.args.get("search"),
                role=request.args.get("role"),
                is_active=is_active,
                page=page,
                per_page=per_page,
            ),
            "Admin users retrieved.",
        )

    @staticmethod
    def update_user(user_id):
        target = db.session.get(User, user_id)
        if not target:
            return error_response("User not found.", 404)
        cleaned, errors = validate_admin_user_update(request.get_json(silent=True))
        if errors:
            return error_response("Validation failed.", 400, errors)
        user, message, status = AdminService.update_user(
            target, cleaned, g.admin_user.id
        )
        if not user:
            return error_response(message, status)
        return success_response({"user": user.to_dict()}, "User updated successfully.")

    @classmethod
    def advertisements(cls):
        page, per_page = cls._pagination()
        return success_response(
            AdminService.advertisements(
                status=request.args.get("status"), page=page, per_page=per_page
            ),
            "Advertising orders retrieved.",
        )

    @staticmethod
    def moderate_advertisement(order_id):
        order = db.session.get(AdvertisingOrder, order_id)
        if not order:
            return error_response("Advertising order not found.", 404)
        data = request.get_json(silent=True) or {}
        next_status = data.get("review_status")
        if next_status not in ADVERTISEMENT_REVIEW_STATUSES:
            return error_response(
                "Validation failed.",
                400,
                {"review_status": "A valid moderation status is required."},
            )
        order, message, status = AdminService.moderate_advertisement(
            order, next_status, g.admin_user.id
        )
        if not order:
            return error_response(message, status)
        return success_response(
            {"advertisement": AdminService._advertisement_payload(order)},
            "Advertisement updated successfully.",
        )

    @classmethod
    def payments(cls):
        page, per_page = cls._pagination()
        return success_response(
            AdminService.payments(page=page, per_page=per_page),
            "Payment records retrieved.",
        )

    @staticmethod
    def settings():
        return success_response(AdminService.settings(), "Safe admin settings retrieved.")
