from app.extensions import db
from app.utils import utc_now


class Favorite(db.Model):
    __tablename__ = "favorites"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recipe_id = db.Column(
        db.Integer, db.ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    user = db.relationship("User", back_populates="favorites")
    recipe = db.relationship("Recipe", back_populates="favorites")

    __table_args__ = (
        db.UniqueConstraint("user_id", "recipe_id", name="uq_user_recipe_favorite"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "recipe_id": self.recipe_id,
            "created_at": self.created_at.isoformat(),
            "recipe": self.recipe.to_dict() if self.recipe else None,
        }
