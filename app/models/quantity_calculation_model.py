from app.extensions import db
from app.utils import utc_now


class QuantityCalculation(db.Model):
    __tablename__ = "quantity_calculations"

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(
        db.Integer, db.ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dish_id = db.Column(
        db.Integer, db.ForeignKey("dishes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    number_of_people = db.Column(db.Integer, nullable=False)
    calculated_ingredients = db.Column(db.Text, nullable=False)
    calculated_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    profile = db.relationship("UserProfile", back_populates="quantity_calculations")
    dish = db.relationship("Dish", back_populates="quantity_calculations")

    def to_dict(self):
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "dish_id": self.dish_id,
            "number_of_people": self.number_of_people,
            "calculated_ingredients": self.calculated_ingredients,
            "calculated_at": self.calculated_at.isoformat(),
            "dish": self.dish.to_dict() if self.dish else None,
        }
