from sqlalchemy import or_

from app.extensions import db
from app.models import Ingredient, Recipe


def _page_payload(pagination):
    meta = {
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev,
    }
    return {
        "items": [recipe.to_dict() for recipe in pagination.items],
        "meta": meta,
        # Backward-compatible alias
        "pagination": meta,
    }


class RecipeService:
    @staticmethod
    def get_all(page=1, per_page=10, search=None, category=None):
        query = Recipe.query

        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(Recipe.name.ilike(pattern), Recipe.description.ilike(pattern))
            )

        if category:
            query = query.filter(Recipe.category.ilike(category.strip()))

        query = query.order_by(Recipe.name.asc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return _page_payload(pagination)

    @staticmethod
    def get_by_id(recipe_id):
        return db.session.get(Recipe, recipe_id)

    @staticmethod
    def get_by_name(name):
        return Recipe.query.filter(Recipe.name.ilike(name.strip())).first()

    @staticmethod
    def get_by_category(category, page=1, per_page=10):
        query = Recipe.query.filter(Recipe.category.ilike(category.strip())).order_by(
            Recipe.name.asc()
        )
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return _page_payload(pagination)

    @staticmethod
    def create(data):
        if Recipe.query.filter(Recipe.name.ilike(data["name"])).first():
            return None, "A recipe with this name already exists.", 409

        recipe = Recipe(
            name=data["name"],
            category=data["category"],
            description=data.get("description", ""),
            serving_size=data["serving_size"],
            steps=data["steps"],
            image=data.get("image", ""),
        )

        for ing_data in data["ingredients"]:
            recipe.ingredients.append(
                Ingredient(
                    name=ing_data["name"],
                    quantity=ing_data["quantity"],
                    unit=ing_data["unit"],
                )
            )

        db.session.add(recipe)
        db.session.commit()
        return recipe, None, 201

    @staticmethod
    def update(recipe, data):
        if "name" in data and data["name"].lower() != recipe.name.lower():
            existing = Recipe.query.filter(Recipe.name.ilike(data["name"])).first()
            if existing and existing.id != recipe.id:
                return None, "A recipe with this name already exists.", 409

        for field in ("name", "category", "description", "serving_size", "steps", "image"):
            if field in data:
                setattr(recipe, field, data[field])

        if "ingredients" in data:
            Ingredient.query.filter_by(recipe_id=recipe.id).delete()
            for ing_data in data["ingredients"]:
                recipe.ingredients.append(
                    Ingredient(
                        name=ing_data["name"],
                        quantity=ing_data["quantity"],
                        unit=ing_data["unit"],
                    )
                )

        db.session.commit()
        return recipe, None, 200

    @staticmethod
    def delete(recipe):
        db.session.delete(recipe)
        db.session.commit()
        return True, None, 200

    @staticmethod
    def get_all_recipes():
        return Recipe.query.order_by(Recipe.name.asc()).all()
