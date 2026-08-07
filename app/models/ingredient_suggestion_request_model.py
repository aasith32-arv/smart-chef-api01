from app.extensions import db
from app.utils import utc_now


class IngredientSuggestionRequest(db.Model):
    __tablename__ = "ingredient_suggestion_requests"

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(
        db.Integer, db.ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    input_ingredients = db.Column(db.Text, nullable=False)
    suggested_dishes = db.Column(db.Text, nullable=False)
    requested_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    profile = db.relationship("UserProfile", back_populates="suggestion_requests")

    def to_dict(self):
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "input_ingredients": self.input_ingredients,
            "suggested_dishes": self.suggested_dishes,
            "requested_at": self.requested_at.isoformat(),
        }
