from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.utils import utc_now


class UserProfile(db.Model):
    __tablename__ = "user_profiles"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")
    registration_date = db.Column(db.DateTime, default=utc_now, nullable=False)

    dishes = db.relationship(
        "Dish",
        back_populates="creator",
        lazy="dynamic",
    )
    quantity_calculations = db.relationship(
        "QuantityCalculation",
        back_populates="profile",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    suggestion_requests = db.relationship(
        "IngredientSuggestionRequest",
        back_populates="profile",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    favorite_recipes = db.relationship(
        "FavoriteRecipe",
        back_populates="profile",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "role": self.role,
            "registration_date": self.registration_date.isoformat(),
        }
