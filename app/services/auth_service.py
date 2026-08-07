from app.extensions import db
from app.models import User


class AuthService:
    @staticmethod
    def register(data):
        if User.query.filter_by(email=data["email"]).first():
            return None, "Email is already registered.", 409

        if User.query.filter_by(username=data["username"]).first():
            return None, "Username is already taken.", 409

        user = User(
            username=data["username"],
            email=data["email"],
            full_name=data.get("full_name"),
        )
        user.set_password(data["password"])
        db.session.add(user)
        db.session.commit()
        return user, None, 201

    @staticmethod
    def get_by_email(email):
        return User.query.filter_by(email=email).first()

    @staticmethod
    def update_profile(user, data):
        if "email" in data and data["email"] != user.email:
            existing = User.query.filter_by(email=data["email"]).first()
            if existing:
                return None, "Email is already registered.", 409

        if "username" in data and data["username"] != user.username:
            existing = User.query.filter_by(username=data["username"]).first()
            if existing:
                return None, "Username is already taken.", 409

        for field in ("username", "email", "full_name"):
            if field in data:
                setattr(user, field, data[field])

        if "password" in data:
            user.set_password(data["password"])

        db.session.commit()
        return user, None, 200

    @staticmethod
    def delete_profile(user):
        db.session.delete(user)
        db.session.commit()
        return True, None, 200
