from app.extensions import db
from app.utils import utc_now


class Recipe(db.Model):
    __tablename__ = "recipes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False, index=True)
    category = db.Column(db.String(80), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    serving_size = db.Column(db.Integer, nullable=False, default=4)
    steps = db.Column(db.JSON, nullable=False)
    image = db.Column(db.String(500), nullable=True)
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
    favorites = db.relationship(
        "Favorite", back_populates="recipe", cascade="all, delete-orphan", lazy="dynamic"
    )

    def to_dict(self, include_ingredients=True):
        data = {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "serving_size": self.serving_size,
            "steps": self.steps,
            "image": self.image,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_ingredients:
            data["ingredients"] = [ing.to_dict() for ing in self.ingredients]
        return data
