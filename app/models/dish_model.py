from app.extensions import db
from app.utils import utc_now


class Dish(db.Model):
    __tablename__ = "dishes"

    id = db.Column(db.Integer, primary_key=True)
    dish_name = db.Column(db.String(150), nullable=False, index=True)
    category = db.Column(db.String(80), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    default_servings = db.Column(db.Integer, nullable=False, default=4)
    created_by = db.Column(
        db.Integer, db.ForeignKey("user_profiles.id", ondelete="SET NULL"), nullable=True
    )
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    creator = db.relationship("UserProfile", back_populates="dishes")
    ingredients = db.relationship(
        "DishIngredient",
        back_populates="dish",
        cascade="all, delete-orphan",
        lazy="joined",
    )
    steps = db.relationship(
        "RecipeStep",
        back_populates="dish",
        cascade="all, delete-orphan",
        lazy="joined",
        order_by="RecipeStep.step_number",
    )
    quantity_calculations = db.relationship(
        "QuantityCalculation",
        back_populates="dish",
        lazy="dynamic",
    )
    favorite_recipes = db.relationship(
        "FavoriteRecipe",
        back_populates="dish",
        lazy="dynamic",
    )

    def to_dict(self, include_ingredients=False, include_steps=False):
        data = {
            "id": self.id,
            "dish_name": self.dish_name,
            "category": self.category,
            "description": self.description,
            "default_servings": self.default_servings,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
        }
        if include_ingredients:
            data["ingredients"] = [ing.to_dict() for ing in self.ingredients]
        if include_steps:
            data["steps"] = [step.to_dict() for step in self.steps]
        return data
