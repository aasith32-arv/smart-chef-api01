from flask import request
from flask_jwt_extended import get_jwt_identity

from app.services import FavoriteService
from app.utils.responses import error_response, success_response
from app.validators import validate_favorite_create


class FavoriteController:
    @staticmethod
    def list():
        favorites = FavoriteService.get_user_favorites(int(get_jwt_identity()))
        return success_response({"count": len(favorites), "favorites": favorites}, "Favorites retrieved successfully.")

    @staticmethod
    def create():
        cleaned, errors = validate_favorite_create(request.get_json(silent=True))
        if errors:
            return error_response("Validation failed.", 400, errors)
        favorite, message, status = FavoriteService.add_favorite(int(get_jwt_identity()), cleaned["recipe_id"])
        if not favorite:
            return error_response(message, status)
        return success_response({"favorite": favorite.to_dict()}, "Favorite added successfully.", status)

    @staticmethod
    def delete(recipe_id):
        result, message, status = FavoriteService.remove_favorite(int(get_jwt_identity()), recipe_id)
        if not result:
            return error_response(message, status)
        return success_response(message="Favorite removed successfully.")
