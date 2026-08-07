from app.extensions import db
from app.models import Favorite, Recipe


class FavoriteService:
    @staticmethod
    def get_user_favorites(user_id):
        favorites = (
            Favorite.query.filter_by(user_id=user_id)
            .order_by(Favorite.created_at.desc())
            .all()
        )
        return [fav.to_dict() for fav in favorites]

    @staticmethod
    def add_favorite(user_id, recipe_id):
        recipe = db.session.get(Recipe, recipe_id)
        if not recipe:
            return None, "Recipe not found.", 404

        existing = Favorite.query.filter_by(user_id=user_id, recipe_id=recipe_id).first()
        if existing:
            return None, "Recipe is already in favorites.", 409

        favorite = Favorite(user_id=user_id, recipe_id=recipe_id)
        db.session.add(favorite)
        db.session.commit()
        return favorite, None, 201

    @staticmethod
    def remove_favorite(user_id, recipe_id):
        favorite = Favorite.query.filter_by(user_id=user_id, recipe_id=recipe_id).first()
        if not favorite:
            return None, "Favorite not found.", 404

        db.session.delete(favorite)
        db.session.commit()
        return True, None, 200
