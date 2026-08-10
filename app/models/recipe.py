from app.extensions import db
from app.utils import utc_now


class Recipe(db.Model):
    __tablename__ = "recipes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(180), unique=True, nullable=True, index=True)
    category = db.Column(db.String(80), nullable=False, index=True)
    family_id = db.Column(
        db.Integer,
        db.ForeignKey("dish_families.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    description = db.Column(db.Text, nullable=True)
    serving_size = db.Column(db.Integer, nullable=False, default=4)
    steps = db.Column(db.JSON, nullable=False)
    image = db.Column(db.String(500), nullable=True)
    cuisine = db.Column(db.String(80), nullable=True, index=True)
    region = db.Column(db.String(100), nullable=True, index=True)
    protein = db.Column(db.String(80), nullable=True, index=True)
    diet_type = db.Column(db.String(40), nullable=True, index=True)
    difficulty = db.Column(db.String(30), nullable=True)
    prep_time = db.Column(db.Integer, nullable=True)
    cook_time = db.Column(db.Integer, nullable=True)
    spice_level = db.Column(db.String(30), nullable=True)
    tags = db.Column(db.JSON, nullable=True, default=list)
    publication_status = db.Column(
        db.String(20), nullable=False, default="published", index=True
    )
    managed_by_admin = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )

    ingredients = db.relationship(
        "Ingredient",
        back_populates="recipe",
        cascade="all, delete-orphan",
        lazy="joined",
    )
    family = db.relationship("DishFamily", back_populates="recipes")
    favorites = db.relationship(
        "Favorite", back_populates="recipe", cascade="all, delete-orphan", lazy="dynamic"
    )
    cooking_steps = db.relationship(
        "CookingStep",
        back_populates="recipe",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="CookingStep.step_number",
    )

    def to_dict(self, include_ingredients=True):
        data = {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "category": self.category,
            "family_id": self.family_id,
            "family": self.family.to_dict(include_recipe_count=False)
            if self.family
            else None,
            "description": self.description,
            "serving_size": self.serving_size,
            "steps": self.steps,
            "image": self.image,
            "cuisine": self.cuisine,
            "region": self.region,
            "protein": self.protein,
            "diet_type": self.diet_type,
            "difficulty": self.difficulty,
            "prep_time": self.prep_time,
            "cook_time": self.cook_time,
            "spice_level": self.spice_level,
            "tags": self.tags or [],
            "publication_status": self.publication_status,
            "managed_by_admin": self.managed_by_admin,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_ingredients:
            data["ingredients"] = [ing.to_dict() for ing in self.ingredients]
        return data
