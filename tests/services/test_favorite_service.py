from flask_jwt_extended import create_access_token

from app.services.favorite_service import FavoriteService


class TestFavoriteService:
    def test_add_list_remove(self, app, sample_user, sample_recipe):
        favorite, error, status = FavoriteService.add_favorite(
            sample_user.id, sample_recipe.id
        )
        assert status == 201
        assert error is None
        assert favorite.recipe_id == sample_recipe.id

        listed = FavoriteService.get_user_favorites(sample_user.id)
        assert len(listed) == 1
        assert listed[0]["recipe"]["name"] == sample_recipe.name

        ok, error, status = FavoriteService.remove_favorite(
            sample_user.id, sample_recipe.id
        )
        assert ok is True
        assert status == 200
        assert FavoriteService.get_user_favorites(sample_user.id) == []

    def test_add_missing_recipe(self, app, sample_user):
        favorite, error, status = FavoriteService.add_favorite(sample_user.id, 9999)
        assert favorite is None
        assert status == 404

    def test_duplicate_favorite(self, app, sample_user, sample_recipe):
        FavoriteService.add_favorite(sample_user.id, sample_recipe.id)
        favorite, error, status = FavoriteService.add_favorite(
