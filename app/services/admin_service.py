from sqlalchemy import func, or_
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import (
    AdminAuditLog,
    AdvertisingOrder,
    BillingCustomer,
    CookingStep,
    CookingStepIngredient,
    DishFamily,
    Recipe,
    Subscription,
    User,
)
from app.services.recipe_service import RecipeService
from app.utils import slugify

ACTIVE_SUBSCRIPTION_STATUSES = {"active", "trialing"}


def _pagination_meta(pagination):
    return {
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev,
    }


class AdminService:
    """Authorization-agnostic management operations over the existing domain models."""

    @staticmethod
    def _audit(admin_id, action, target_type, target_id=None):
        db.session.add(
            AdminAuditLog(
                admin_user_id=admin_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
            )
        )

    @staticmethod
    def _recipe_payload(recipe, include_cooking_steps=False):
        data = recipe.to_dict()
        data["managed_by_admin"] = recipe.managed_by_admin
        if include_cooking_steps:
            data["cooking_steps"] = [
                {
                    "id": step.id,
                    "step_number": step.step_number,
                    "title": step.title,
                    "instruction": step.instruction,
                    "duration": step.duration,
                    "minimum_duration": step.minimum_duration,
                    "maximum_duration": step.maximum_duration,
                    "heat_level": step.heat_level,
                    "temperature_min": step.temperature_min,
                    "temperature_max": step.temperature_max,
                    "visual_cue": step.visual_cue,
                    "colour_stage": step.colour_stage,
                    "texture_cue": step.texture_cue,
                    "aroma_cue": step.aroma_cue,
                    "transformation_before": step.transformation_before,
                    "transformation_process": step.transformation_process,
                    "transformation_after": step.transformation_after,
                    "purpose": step.purpose,
                    "benefits": step.benefits or [],
                    "warnings": step.warnings or [],
                    "common_mistakes": step.common_mistakes or [],
                    "correction": step.correction,
                    "scientific_explanation": step.scientific_explanation,
                    "critical": step.critical,
                    "ingredient_names": [
                        addition.ingredient_name for addition in step.ingredient_additions
                    ],
                }
                for step in recipe.cooking_steps
            ]
        return data

    @classmethod
    def dashboard(cls):
        active_subscription_users = (
            db.session.query(func.count(func.distinct(Subscription.user_id)))
            .filter(Subscription.status.in_(ACTIVE_SUBSCRIPTION_STATUSES))
            .scalar()
            or 0
        )
        statistics = {
            "total_recipes": Recipe.query.count(),
            "total_families": DishFamily.query.count(),
            "total_users": User.query.count(),
            "premium_users": active_subscription_users,
            "published_recipes": Recipe.query.filter_by(publication_status="published").count(),
            "draft_recipes": Recipe.query.filter_by(publication_status="draft").count(),
            "inactive_recipes": Recipe.query.filter_by(publication_status="inactive").count(),
            "total_advertisements": AdvertisingOrder.query.count(),
            "pending_advertisements": AdvertisingOrder.query.filter_by(
                review_status="under_review"
            ).count(),
        }
        recent_recipes = (
            Recipe.query.options(selectinload(Recipe.family))
            .order_by(Recipe.created_at.desc())
            .limit(5)
            .all()
        )
        recent_updated_recipes = (
            Recipe.query.options(selectinload(Recipe.family))
            .order_by(Recipe.updated_at.desc())
            .limit(5)
            .all()
        )
        recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
        recent_orders = (
            AdvertisingOrder.query.options(selectinload(AdvertisingOrder.user))
            .order_by(AdvertisingOrder.created_at.desc())
            .limit(5)
            .all()
        )
        recent_audit = (
            AdminAuditLog.query.options(selectinload(AdminAuditLog.admin))
            .order_by(AdminAuditLog.created_at.desc())
            .limit(8)
            .all()
        )
        return {
            "statistics": statistics,
            "recent_recipes": [cls._recipe_payload(item) for item in recent_recipes],
            "recent_updated_recipes": [
                cls._recipe_payload(item) for item in recent_updated_recipes
            ],
            "recent_users": [item.to_dict() for item in recent_users],
            "recent_advertisements": [cls._advertisement_payload(item) for item in recent_orders],
            "recent_audit": [item.to_dict() for item in recent_audit],
        }

    @classmethod
    def recipes(cls, **filters):
        return RecipeService.get_all(include_unpublished=True, **filters)

    @classmethod
    def recipe(cls, recipe_id):
        recipe = RecipeService.get_by_id(recipe_id, include_unpublished=True)
        return cls._recipe_payload(recipe, include_cooking_steps=True) if recipe else None

    @staticmethod
    def _unique_slug(name, recipe_id=None):
        base = slugify(name) or "recipe"
        candidate = base
        number = 2
        while True:
            query = Recipe.query.filter(Recipe.slug.ilike(candidate))
            if recipe_id is not None:
                query = query.filter(Recipe.id != recipe_id)
            if not query.first():
                return candidate
            candidate = f"{base}-{number}"
            number += 1

    @staticmethod
    def _sync_cooking_steps(recipe, cooking_steps):
        recipe.cooking_steps.clear()
        db.session.flush()
        ingredients_by_name = {
            ingredient.name.strip().casefold(): ingredient for ingredient in recipe.ingredients
        }
        for number, item in enumerate(cooking_steps or [], start=1):
            step = CookingStep(
                step_number=number,
                title=item["title"],
                instruction=item["instruction"],
                duration=item.get("duration"),
                minimum_duration=item.get("minimum_duration"),
                maximum_duration=item.get("maximum_duration"),
                heat_level=item.get("heat_level"),
                temperature_min=item.get("temperature_min"),
                temperature_max=item.get("temperature_max"),
                visual_cue=item.get("visual_cue"),
                colour_stage=item.get("colour_stage"),
                texture_cue=item.get("texture_cue"),
                aroma_cue=item.get("aroma_cue"),
                transformation_before=item.get("transformation_before"),
                transformation_process=item.get("transformation_process"),
                transformation_after=item.get("transformation_after"),
                purpose=item.get("purpose"),
                benefits=item.get("benefits", []),
                warnings=item.get("warnings", []),
                common_mistakes=item.get("common_mistakes", []),
                correction=item.get("correction"),
                scientific_explanation=item.get("scientific_explanation"),
                critical=item.get("critical", False),
                source="curated",
            )
            for addition_order, name in enumerate(item.get("ingredient_names", []), start=1):
                ingredient = ingredients_by_name.get(name.strip().casefold())
                if ingredient:
                    step.ingredient_additions.append(
                        CookingStepIngredient(
                            ingredient=ingredient,
                            ingredient_name=ingredient.name,
                            quantity=ingredient.quantity,
                            unit=ingredient.unit,
                            addition_order=addition_order,
                        )
                    )
            recipe.cooking_steps.append(step)

    @staticmethod
    def _missing_cooking_ingredients(cooking_steps, ingredients):
        available = {
            ingredient["name"].strip().casefold()
            if isinstance(ingredient, dict)
            else ingredient.name.strip().casefold()
            for ingredient in ingredients
        }
        return sorted(
            {
                name
                for step in cooking_steps or []
                for name in step.get("ingredient_names", [])
                if name.strip().casefold() not in available
            },
            key=str.casefold,
        )

    @classmethod
    def create_recipe(cls, data, admin_id):
        payload = dict(data)
        cooking_steps = payload.pop("cooking_steps", [])
        missing = cls._missing_cooking_ingredients(cooking_steps, payload.get("ingredients", []))
        if missing:
            return None, f"Cooking steps reference unknown ingredients: {', '.join(missing)}.", 400
        payload["slug"] = payload.get("slug") or cls._unique_slug(payload["name"])
        payload["managed_by_admin"] = True
        recipe, message, status = RecipeService.create(payload, commit=False)
        if not recipe:
            db.session.rollback()
            return None, message, status
        cls._sync_cooking_steps(recipe, cooking_steps)
        cls._audit(admin_id, "CREATED_RECIPE", "recipe", recipe.id)
        db.session.commit()
        return recipe, None, 201

    @classmethod
    def update_recipe(cls, recipe, data, admin_id):
        payload = dict(data)
        cooking_steps = payload.pop("cooking_steps", None)
        if cooking_steps is not None:
            missing = cls._missing_cooking_ingredients(
                cooking_steps, payload.get("ingredients", recipe.ingredients)
            )
            if missing:
                return (
                    None,
                    f"Cooking steps reference unknown ingredients: {', '.join(missing)}.",
                    400,
                )
        if "name" in payload and not payload.get("slug") and not recipe.slug:
            payload["slug"] = cls._unique_slug(payload["name"], recipe.id)
        payload["managed_by_admin"] = True
        updated, message, status = RecipeService.update(recipe, payload, commit=False)
        if not updated:
            db.session.rollback()
            return None, message, status
        if cooking_steps is not None:
            cls._sync_cooking_steps(recipe, cooking_steps)
        cls._audit(admin_id, "UPDATED_RECIPE", "recipe", recipe.id)
        db.session.commit()
        return recipe, None, 200

    @classmethod
    def duplicate_recipe(cls, recipe, admin_id):
        base_name = f"{recipe.name} Copy"
        name = base_name
        number = 2
        while Recipe.query.filter(Recipe.name.ilike(name)).first():
            name = f"{base_name} {number}"
            number += 1
        payload = {
            "name": name,
            "slug": cls._unique_slug(name),
            "category": recipe.category,
            "family_id": recipe.family_id,
            "description": recipe.description or "",
            "serving_size": recipe.serving_size,
            "steps": list(recipe.steps or []),
            "image": recipe.image or "",
            "cuisine": recipe.cuisine,
            "region": recipe.region,
            "protein": recipe.protein,
            "diet_type": recipe.diet_type,
            "difficulty": recipe.difficulty,
            "prep_time": recipe.prep_time,
            "cook_time": recipe.cook_time,
            "spice_level": recipe.spice_level,
            "tags": list(recipe.tags or []),
            "publication_status": "draft",
            "ingredients": [item.to_dict() for item in recipe.ingredients],
            "cooking_steps": cls._recipe_payload(recipe, include_cooking_steps=True)[
                "cooking_steps"
            ],
        }
        copy, message, status = cls.create_recipe(payload, admin_id)
        if copy:
            audit = (
                AdminAuditLog.query.filter_by(
                    admin_user_id=admin_id,
                    action="CREATED_RECIPE",
                    target_id=copy.id,
                )
                .order_by(AdminAuditLog.id.desc())
                .first()
            )
            if audit:
                audit.action = "DUPLICATED_RECIPE"
                db.session.commit()
        return copy, message, status

    @classmethod
    def deactivate_recipe(cls, recipe, admin_id):
        recipe.publication_status = "inactive"
        recipe.managed_by_admin = True
        cls._audit(admin_id, "DEACTIVATED_RECIPE", "recipe", recipe.id)
        db.session.commit()
        return recipe

    @classmethod
    def families(cls, search=None, page=1, per_page=20):
        query = DishFamily.query
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    DishFamily.name.ilike(pattern),
                    DishFamily.slug.ilike(pattern),
                    DishFamily.category.ilike(pattern),
                )
            )
        pagination = query.order_by(DishFamily.name).paginate(
            page=page, per_page=per_page, error_out=False
        )
        ids = [family.id for family in pagination.items]
        counts = (
            dict(
                db.session.query(Recipe.family_id, func.count(Recipe.id))
                .filter(Recipe.family_id.in_(ids))
                .group_by(Recipe.family_id)
                .all()
            )
            if ids
            else {}
        )
        return {
            "items": [
                {
                    **family.to_dict(recipe_count=counts.get(family.id, 0)),
                    "managed_by_admin": family.managed_by_admin,
                }
                for family in pagination.items
            ],
            "meta": _pagination_meta(pagination),
        }

    @classmethod
    def create_family(cls, data, admin_id):
        if DishFamily.query.filter(
            or_(
                DishFamily.name.ilike(data["name"]),
                DishFamily.slug.ilike(data["slug"]),
            )
        ).first():
            return None, "Dish family name or slug already exists.", 409
        family = DishFamily(**data, managed_by_admin=True)
        db.session.add(family)
        db.session.flush()
        cls._audit(admin_id, "CREATED_FAMILY", "dish_family", family.id)
        db.session.commit()
        return family, None, 201

    @classmethod
    def update_family(cls, family, data, admin_id):
        for field in ("name", "slug"):
            if field in data:
                existing = DishFamily.query.filter(
                    getattr(DishFamily, field).ilike(data[field]),
                    DishFamily.id != family.id,
                ).first()
                if existing:
                    return None, f"Dish family {field} already exists.", 409
        for field, value in data.items():
            setattr(family, field, value)
        family.managed_by_admin = True
        cls._audit(admin_id, "UPDATED_FAMILY", "dish_family", family.id)
        db.session.commit()
        return family, None, 200

    @classmethod
    def delete_family(cls, family, admin_id):
        if Recipe.query.filter_by(family_id=family.id).count():
            return False, "Reassign its recipes before deleting this dish family.", 409
        family_id = family.id
        db.session.delete(family)
        cls._audit(admin_id, "DELETED_FAMILY", "dish_family", family_id)
        db.session.commit()
        return True, None, 200

    @staticmethod
    def categories():
        recipe_counts = dict(
            db.session.query(Recipe.category, func.count(Recipe.id)).group_by(Recipe.category).all()
        )
        family_counts = dict(
            db.session.query(DishFamily.category, func.count(DishFamily.id))
            .group_by(DishFamily.category)
            .all()
        )
        names = sorted(set(recipe_counts) | set(family_counts), key=str.casefold)
        return [
            {
                "name": name,
                "recipe_count": recipe_counts.get(name, 0),
                "family_count": family_counts.get(name, 0),
            }
            for name in names
        ]

    @classmethod
    def rename_category(cls, old_name, new_name, admin_id):
        recipes = Recipe.query.filter(Recipe.category.ilike(old_name)).all()
        families = DishFamily.query.filter(DishFamily.category.ilike(old_name)).all()
        if not recipes and not families:
            return None
        for recipe in recipes:
            recipe.category = new_name
            recipe.managed_by_admin = True
        for family in families:
            family.category = new_name
            family.managed_by_admin = True
        cls._audit(admin_id, "RENAMED_CATEGORY", "category", None)
        db.session.commit()
        return {"recipes_updated": len(recipes), "families_updated": len(families)}

    @staticmethod
    def users(search=None, role=None, is_active=None, page=1, per_page=20):
        query = User.query
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    User.username.ilike(pattern),
                    User.email.ilike(pattern),
                    User.full_name.ilike(pattern),
                )
            )
        if role:
            query = query.filter(User.role == role)
        if is_active is not None:
            query = query.filter(User.is_active.is_(is_active))
        pagination = query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        ids = [user.id for user in pagination.items]
        premium_ids = (
            {
                user_id
                for (user_id,) in db.session.query(Subscription.user_id)
                .filter(
                    Subscription.user_id.in_(ids),
                    Subscription.status.in_(ACTIVE_SUBSCRIPTION_STATUSES),
                )
                .distinct()
                .all()
            }
            if ids
            else set()
        )
        return {
            "items": [
                {**user.to_dict(), "is_premium": user.id in premium_ids}
                for user in pagination.items
            ],
            "meta": _pagination_meta(pagination),
        }

    @classmethod
    def update_user(cls, target, data, admin_id):
        if target.id == admin_id and (data.get("role") == "user" or data.get("is_active") is False):
            return None, "You cannot demote or suspend your own admin account.", 409
        removing_active_admin = (
            target.role == "admin"
            and target.is_active
            and (data.get("role") == "user" or data.get("is_active") is False)
        )
        if removing_active_admin:
            active_admins = User.query.filter_by(role="admin", is_active=True).count()
            if active_admins <= 1:
                return None, "The final active admin account cannot be removed.", 409
        action = "UPDATED_USER"
        if "role" in data and data["role"] != target.role:
            action = "CHANGED_USER_ROLE"
        elif "is_active" in data and data["is_active"] != target.is_active:
            action = "SUSPENDED_USER" if not data["is_active"] else "ACTIVATED_USER"
        for field, value in data.items():
            setattr(target, field, value)
        cls._audit(admin_id, action, "user", target.id)
        db.session.commit()
        return target, None, 200

    @staticmethod
    def _advertisement_payload(order):
        return {
            **order.to_dict(),
            "updated_at": order.updated_at.isoformat(),
            "customer": {
                "id": order.user.id,
                "username": order.user.username,
                "email": order.user.email,
            }
            if order.user
            else None,
        }

    @classmethod
    def advertisements(cls, status=None, page=1, per_page=20):
        query = AdvertisingOrder.query.options(selectinload(AdvertisingOrder.user))
        if status:
            query = query.filter(AdvertisingOrder.review_status == status)
        pagination = query.order_by(AdvertisingOrder.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        return {
            "items": [cls._advertisement_payload(item) for item in pagination.items],
            "meta": _pagination_meta(pagination),
        }

    @classmethod
    def moderate_advertisement(cls, order, next_status, admin_id):
        transitions = {
            "under_review": {"approved", "rejected"},
            "approved": {"active", "rejected"},
            "active": {"completed"},
        }
        if order.payment_status != "paid":
            return None, "Only Stripe-confirmed paid orders can be moderated.", 409
        if next_status not in transitions.get(order.review_status, set()):
            return None, "That advertisement status transition is not allowed.", 409
        order.review_status = next_status
        cls._audit(
            admin_id,
            f"ADVERTISEMENT_{next_status.upper()}",
            "advertising_order",
            order.id,
        )
        db.session.commit()
        return order, None, 200

    @staticmethod
    def payments(page=1, per_page=20):
        pagination = (
            Subscription.query.options(selectinload(Subscription.user))
            .order_by(Subscription.updated_at.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )
        user_ids = [item.user_id for item in pagination.items]
        customers = (
            {
                item.user_id: item.stripe_customer_id
                for item in BillingCustomer.query.filter(
                    BillingCustomer.user_id.in_(user_ids)
                ).all()
            }
            if user_ids
            else {}
        )
        return {
            "items": [
                {
                    "id": item.id,
                    "user": {
                        "id": item.user.id,
                        "username": item.user.username,
                        "email": item.user.email,
                    },
                    "stripe_customer_id": customers.get(item.user_id),
                    "stripe_subscription_id": item.stripe_subscription_id,
                    "stripe_price_id": item.stripe_price_id,
                    "status": item.status,
                    "current_period_end": item.current_period_end.isoformat()
                    if item.current_period_end
                    else None,
                    "cancel_at_period_end": item.cancel_at_period_end,
                    "created_at": item.created_at.isoformat(),
                    "updated_at": item.updated_at.isoformat(),
                }
                for item in pagination.items
            ],
            "meta": _pagination_meta(pagination),
        }

    @staticmethod
    def settings():
        return {
            "catalog": {
                "publication_statuses": ["draft", "published", "inactive"],
                "difficulty_levels": ["Easy", "Medium", "Advanced"],
                "spice_levels": ["Mild", "Medium", "Hot"],
                "category_source": "Recipes and dish families",
            },
            "billing": {
                "currency": "LKR",
                "subscription_amount": 1200,
                "advertising_amount": 2000,
                "source_of_truth": "Stripe webhooks",
            },
            "security": {
                "admin_authorization": "Backend role validation",
                "cookie_authentication": True,
                "csrf_protection": True,
                "sensitive_settings_location": "Server environment only",
            },
        }
