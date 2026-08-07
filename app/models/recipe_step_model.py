from app.extensions import db


class RecipeStep(db.Model):
    __tablename__ = "recipe_steps"

    id = db.Column(db.Integer, primary_key=True)
    dish_id = db.Column(
        db.Integer, db.ForeignKey("dishes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    step_number = db.Column(db.Integer, nullable=False)
    instruction = db.Column(db.Text, nullable=False)

    dish = db.relationship("Dish", back_populates="steps")

    def to_dict(self):
        return {
            "id": self.id,
            "dish_id": self.dish_id,
            "step_number": self.step_number,
            "instruction": self.instruction,
        }
