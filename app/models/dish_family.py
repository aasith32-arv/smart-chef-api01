from app.extensions import db
from app.utils import utc_now


class DishFamily(db.Model):
    """A discoverable family that groups recipe varieties without replacing recipes."""

    __tablename__ = "dish_families"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(140), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(80), nullable=False, index=True)
    image = db.Column(db.String(500), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    managed_by_admin = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )

    recipes = db.relationship(
        "Recipe",
        back_populates="family",
        lazy="select",
    )

    def to_dict(self, include_recipe_count=True, recipe_count=None):
        data = {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "category": self.category,
            "image": self.image,
            "is_active": self.is_active,
        }
        if include_recipe_count:
            if recipe_count is None:
                from app.models.recipe import Recipe

                recipe_count = Recipe.query.filter_by(
                    family_id=self.id, publication_status="published"
                ).count()
            data["recipe_count"] = recipe_count
        return data
