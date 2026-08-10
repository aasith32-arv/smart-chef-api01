from sqlalchemy import String, cast, or_
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import DishFamily, Ingredient, Recipe


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
    def get_all(
        page=1,
        per_page=10,
        search=None,
        category=None,
        family=None,
        cuisine=None,
        region=None,
        protein=None,
        diet_type=None,
        difficulty=None,
        spice_level=None,
        max_cook_time=None,
        publication_status=None,
        include_unpublished=False,
    ):
        query = Recipe.query.options(selectinload(Recipe.family))

        if not include_unpublished:
            query = query.filter(Recipe.publication_status == "published")
        elif publication_status:
            query = query.filter(Recipe.publication_status == publication_status)

        if search and search.strip():
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Recipe.name.ilike(pattern),
                    Recipe.description.ilike(pattern),
                    Recipe.category.ilike(pattern),
                    Recipe.cuisine.ilike(pattern),
                    Recipe.region.ilike(pattern),
                    Recipe.protein.ilike(pattern),
                    cast(Recipe.tags, String).ilike(pattern),
                    Recipe.family.has(
                        or_(
                            DishFamily.name.ilike(pattern),
                            DishFamily.slug.ilike(pattern),
                        )
                    ),
                )
            )

        if category:
            query = query.filter(Recipe.category.ilike(category.strip()))
        if family:
            query = query.filter(Recipe.family.has(DishFamily.slug.ilike(family.strip())))
        for column, value in (
            (Recipe.cuisine, cuisine),
            (Recipe.region, region),
            (Recipe.protein, protein),
            (Recipe.diet_type, diet_type),
            (Recipe.difficulty, difficulty),
            (Recipe.spice_level, spice_level),
        ):
            if value:
                query = query.filter(column.ilike(value.strip()))
        if max_cook_time is not None and max_cook_time > 0:
            query = query.filter(Recipe.cook_time <= max_cook_time)

        query = query.order_by(Recipe.name.asc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return _page_payload(pagination)

    @staticmethod
    def get_by_id(recipe_id, include_unpublished=False):
        query = Recipe.query.options(selectinload(Recipe.family)).filter_by(id=recipe_id)
        if not include_unpublished:
            query = query.filter(Recipe.publication_status == "published")
        return query.first()

    @staticmethod
    def get_by_name(name):
        return Recipe.query.filter(
            Recipe.name.ilike(name.strip()),
            Recipe.publication_status == "published",
        ).first()

    @staticmethod
    def get_by_category(category, page=1, per_page=10):
        query = Recipe.query.filter(
            Recipe.category.ilike(category.strip()),
            Recipe.publication_status == "published",
        ).order_by(Recipe.name.asc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return _page_payload(pagination)

    @staticmethod
    def create(data, *, commit=True):
        if Recipe.query.filter(Recipe.name.ilike(data["name"])).first():
            return None, "A recipe with this name already exists.", 409
        if data.get("slug") and Recipe.query.filter(Recipe.slug.ilike(data["slug"])).first():
            return None, "A recipe with this slug already exists.", 409
        if data.get("family_id") and not db.session.get(DishFamily, data["family_id"]):
            return None, "Dish family not found.", 400

        recipe = Recipe(
            name=data["name"],
            slug=data.get("slug"),
            category=data["category"],
            family_id=data.get("family_id"),
            description=data.get("description", ""),
            serving_size=data["serving_size"],
            steps=data["steps"],
            image=data.get("image", ""),
            cuisine=data.get("cuisine"),
            region=data.get("region"),
            protein=data.get("protein"),
            diet_type=data.get("diet_type"),
            difficulty=data.get("difficulty"),
            prep_time=data.get("prep_time"),
            cook_time=data.get("cook_time"),
            spice_level=data.get("spice_level"),
            tags=data.get("tags", []),
            publication_status=data.get("publication_status", "published"),
            managed_by_admin=bool(data.get("managed_by_admin", False)),
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
        if commit:
            db.session.commit()
        else:
            db.session.flush()
        return recipe, None, 201

    @staticmethod
    def update(recipe, data, *, commit=True):
        if "name" in data and data["name"].lower() != recipe.name.lower():
            existing = Recipe.query.filter(Recipe.name.ilike(data["name"])).first()
            if existing and existing.id != recipe.id:
                return None, "A recipe with this name already exists.", 409
        if "slug" in data and data["slug"]:
            existing = Recipe.query.filter(Recipe.slug.ilike(data["slug"])).first()
            if existing and existing.id != recipe.id:
                return None, "A recipe with this slug already exists.", 409
        if data.get("family_id") and not db.session.get(DishFamily, data["family_id"]):
            return None, "Dish family not found.", 400

        for field in (
            "name",
            "slug",
            "category",
            "family_id",
            "description",
            "serving_size",
            "steps",
            "image",
            "cuisine",
            "region",
            "protein",
            "diet_type",
            "difficulty",
            "prep_time",
            "cook_time",
            "spice_level",
            "tags",
            "publication_status",
            "managed_by_admin",
        ):
            if field in data:
                setattr(recipe, field, data[field])

        if "ingredients" in data:
            recipe.ingredients.clear()
            db.session.flush()
            for ing_data in data["ingredients"]:
                recipe.ingredients.append(
                    Ingredient(
                        name=ing_data["name"],
                        quantity=ing_data["quantity"],
                        unit=ing_data["unit"],
                    )
                )

        if commit:
            db.session.commit()
        else:
            db.session.flush()
        return recipe, None, 200

    @staticmethod
    def delete(recipe, *, commit=True):
        db.session.delete(recipe)
        if commit:
            db.session.commit()
        else:
            db.session.flush()
        return True, None, 200

    @staticmethod
    def get_all_recipes():
        return Recipe.query.filter_by(publication_status="published").order_by(
            Recipe.name.asc()
        ).all()
