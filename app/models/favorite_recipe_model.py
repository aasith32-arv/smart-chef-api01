from app.extensions import db
from app.utils import utc_now


class FavoriteRecipe(db.Model):
    __tablename__ = "favorite_recipes"

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(
        db.Integer, db.ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dish_id = db.Column(
        db.Integer, db.ForeignKey("dishes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    saved_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    profile = db.relationship("UserProfile", back_populates="favorite_recipes")
    dish = db.relationship("Dish", back_populates="favorite_recipes")

    __table_args__ = (
        db.UniqueConstraint("profile_id", "dish_id", name="uq_profile_dish_favorite"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "dish_id": self.dish_id,
            "saved_at": self.saved_at.isoformat(),
            "dish": self.dish.to_dict() if self.dish else None,
        }
