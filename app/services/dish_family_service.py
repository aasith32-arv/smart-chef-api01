from sqlalchemy import and_, func, or_

from app.extensions import db
from app.models import DishFamily, Recipe


class DishFamilyService:
    """Read-only discovery service for active dish families and their recipes."""

    @staticmethod
    def get_all(category=None, search=None):
        query = DishFamily.query.filter(DishFamily.is_active.is_(True))

        if category:
            query = query.filter(DishFamily.category.ilike(category.strip()))

        if search and search.strip():
            pattern = f"%{search.strip()}%"
            recipe_match = DishFamily.recipes.any(
                and_(
                    Recipe.publication_status == "published",
                    or_(
                        Recipe.name.ilike(pattern),
                        Recipe.cuisine.ilike(pattern),
                        Recipe.region.ilike(pattern),
                        Recipe.protein.ilike(pattern),
                    ),
                )
            )
            query = query.filter(
                or_(
                    DishFamily.name.ilike(pattern),
                    DishFamily.description.ilike(pattern),
                    DishFamily.category.ilike(pattern),
                    recipe_match,
                )
            )

        families = query.order_by(DishFamily.name).all()
        ids = [family.id for family in families]
        counts = {}
        if ids:
            counts = dict(
                db.session.query(Recipe.family_id, func.count(Recipe.id))
                .filter(
                    Recipe.family_id.in_(ids),
                    Recipe.publication_status == "published",
                )
                .group_by(Recipe.family_id)
                .all()
            )
        return [
            family.to_dict(recipe_count=counts.get(family.id, 0))
            for family in families
        ]

    @staticmethod
    def get_by_slug(slug):
        return DishFamily.query.filter(
            DishFamily.slug.ilike(slug.strip()),
            DishFamily.is_active.is_(True),
        ).first()
