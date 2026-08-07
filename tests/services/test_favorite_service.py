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
            sample_user.id, sample_recipe.id
        )
        assert favorite is None
        assert status == 409

    def test_remove_missing_favorite(self, app, sample_user, sample_recipe):
        ok, error, status = FavoriteService.remove_favorite(
            sample_user.id, sample_recipe.id
        )
        assert ok is None
        assert status == 404


class TestFavoriteAuthEnforcement:
    def test_favorites_require_auth(self, client):
        response = client.get("/api/v1/favorites")
        assert response.status_code == 401

    def test_favorites_with_bearer_token(self, client, sample_user, sample_recipe):
        token = create_access_token(identity=str(sample_user.id))
        headers = {"Authorization": f"Bearer {token}"}

        add = client.post(
            "/api/v1/favorites",
            json={"recipe_id": sample_recipe.id},
            headers=headers,
        )
        assert add.status_code == 201

        listed = client.get("/api/v1/favorites", headers=headers)
        assert listed.status_code == 200
        payload = listed.get_json()
        assert payload["success"] is True
        assert len(payload["data"]["favorites"]) == 1
