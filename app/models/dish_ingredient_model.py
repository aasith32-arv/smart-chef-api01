from app.extensions import db

VALID_UNITS = ("g", "kg", "ml", "l", "tsp", "tbsp", "pcs")


class DishIngredient(db.Model):
    __tablename__ = "dish_ingredients"

    id = db.Column(db.Integer, primary_key=True)
    dish_id = db.Column(
        db.Integer, db.ForeignKey("dishes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ingredient_name = db.Column(db.String(120), nullable=False)
    quantity_per_serving = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(10), nullable=False)

    dish = db.relationship("Dish", back_populates="ingredients")

    def to_dict(self):
        return {
            "id": self.id,
            "dish_id": self.dish_id,
            "ingredient_name": self.ingredient_name,
            "quantity_per_serving": self.quantity_per_serving,
            "unit": self.unit,
        }
