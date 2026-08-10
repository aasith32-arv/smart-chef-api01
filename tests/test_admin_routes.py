from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models import AdvertisingOrder, DishFamily, Favorite, Recipe, User
from app.seeders import seed_recipes


def auth_headers(app, user):
    with app.app_context():
        token = create_access_token(
            identity=str(user.id), additional_claims={"role": user.role}
        )
    return {"Authorization": f"Bearer {token}"}


def make_admin():
    admin = User(
        username="admin",
        email="admin@example.com",
        role="admin",
        is_active=True,
    )
    admin.set_password("safe-admin-password")
    db.session.add(admin)
    db.session.commit()
    return admin


def recipe_payload(**overrides):
    payload = {
        "name": "Admin Lentil Curry",
        "category": "Curries",
        "description": "A production-managed lentil curry.",
        "serving_size": 4,
        "steps": ["Wash the lentils.", "Simmer until tender."],
        "ingredients": [
            {"name": "Red Lentils", "quantity": 400, "unit": "g"},
            {"name": "Water", "quantity": 800, "unit": "ml"},
        ],
        "difficulty": "Easy",
        "publication_status": "published",
        "cooking_steps": [
            {
                "title": "Simmer lentils",
                "instruction": "Simmer gently until the lentils are tender.",
                "duration": 20,
                "heat_level": "LOW",
                "visual_cue": "The lentils lose their sharp edges.",
                "ingredient_names": ["Red Lentils"],
                "critical": False,
            }
        ],
    }
    payload.update(overrides)
    return payload


def test_create_admin_cli_is_controlled(app):
    runner = app.test_cli_runner()
    result = runner.invoke(
        args=[
            "create-admin",
            "--email",
            "cli-admin@example.com",
            "--username",
            "cli-admin",
            "--password",
            "a-secure-admin-password",
        ]
    )
    assert result.exit_code == 0
    admin = User.query.filter_by(email="cli-admin@example.com").one()
    assert admin.role == "admin"
    assert admin.is_active is True
    assert admin.password_hash != "a-secure-admin-password"

    duplicate = runner.invoke(
        args=[
            "create-admin",
            "--email",
            "cli-admin@example.com",
            "--username",
            "another-admin",
            "--password",
            "another-secure-password",
        ]
    )
    assert duplicate.exit_code != 0


def test_password_reset_cli_recovers_existing_account(app, sample_user):
    runner = app.test_cli_runner()
    result = runner.invoke(
        args=[
            "reset-user-password",
            "--email",
            sample_user.email,
            "--password",
            "a-new-secure-password",
        ]
    )
    assert result.exit_code == 0
    db.session.refresh(sample_user)
    assert sample_user.check_password("a-new-secure-password") is True

    missing = runner.invoke(
        args=[
            "reset-user-password",
            "--email",
            "missing@example.com",
            "--password",
            "another-secure-password",
        ]
    )
    assert missing.exit_code != 0


def test_normal_user_cannot_access_admin_api(app, client, sample_user):
    response = client.get(
        "/api/v1/admin/dashboard", headers=auth_headers(app, sample_user)
    )
    assert response.status_code == 403
    assert "permission" in response.get_json()["message"].lower()


def test_public_registration_cannot_create_admin(client):
    response = client.post(
        "/api/v1/register",
        json={
            "username": "public-user",
            "email": "public@example.com",
            "password": "secret12",
            "role": "admin",
            "is_active": False,
        },
    )
    assert response.status_code == 201
    user = User.query.filter_by(email="public@example.com").one()
    assert user.role == "user"
    assert user.is_active is True


def test_admin_dashboard_uses_real_counts(app, client, sample_recipe, sample_user):
    admin = make_admin()
    response = client.get(
        "/api/v1/admin/dashboard", headers=auth_headers(app, admin)
    )
    assert response.status_code == 200
    stats = response.get_json()["data"]["statistics"]
    assert stats["total_recipes"] == 1
    assert stats["total_users"] == 2
    assert stats["published_recipes"] == 1


def test_admin_recipe_integrates_with_public_features(app, client, sample_user):
    admin = make_admin()
    response = client.post(
        "/api/v1/admin/recipes",
        headers=auth_headers(app, admin),
        json=recipe_payload(),
    )
    assert response.status_code == 201
    recipe = Recipe.query.filter_by(name="Admin Lentil Curry").one()
    assert recipe.managed_by_admin is True
    assert recipe.slug == "admin-lentil-curry"
    assert len(recipe.cooking_steps) == 1

    public = client.get(f"/api/v1/recipes/{recipe.id}")
    assert public.status_code == 200

    scaled = client.post(
        "/api/v1/calculate", json={"recipe": recipe.name, "people": 40}
    )
    assert scaled.status_code == 200
    assert scaled.get_json()["data"]["quantities"]["Red Lentils"] == "4 kg"

    recommendations = client.post(
        "/api/v1/recommend", json={"ingredients": ["red lentil", "water"]}
    )
    assert recommendations.status_code == 200
    names = [
        item["recipe"]["name"]
        for item in recommendations.get_json()["data"]["recommendations"]
    ]
    assert recipe.name in names

    cooking = client.get(f"/api/v1/recipes/{recipe.id}/cooking-plan")
    assert cooking.status_code == 200
    assert cooking.get_json()["data"]["source"] == "stored"
    assert cooking.get_json()["data"]["steps"][0]["ingredients"][0]["name"] == "Red Lentils"

    db.session.add(Favorite(user_id=sample_user.id, recipe_id=recipe.id))
    db.session.commit()
    updated = client.put(
        f"/api/v1/admin/recipes/{recipe.id}",
        headers=auth_headers(app, admin),
        json={"description": "Updated without replacing the recipe ID."},
    )
    assert updated.status_code == 200
    assert Favorite.query.filter_by(recipe_id=recipe.id).count() == 1


def test_draft_and_inactive_recipes_are_hidden_publicly(app, client):
    admin = make_admin()
    created = client.post(
        "/api/v1/admin/recipes",
        headers=auth_headers(app, admin),
        json=recipe_payload(name="Private Draft", publication_status="draft"),
    )
    assert created.status_code == 201
    recipe_id = created.get_json()["data"]["recipe"]["id"]
    assert client.get(f"/api/v1/recipes/{recipe_id}").status_code == 404

    published = client.put(
        f"/api/v1/admin/recipes/{recipe_id}",
        headers=auth_headers(app, admin),
        json={"publication_status": "published"},
    )
    assert published.status_code == 200
    assert client.get(f"/api/v1/recipes/{recipe_id}").status_code == 200

    deleted = client.delete(
        f"/api/v1/admin/recipes/{recipe_id}", headers=auth_headers(app, admin)
    )
    assert deleted.status_code == 200
    assert client.get(f"/api/v1/recipes/{recipe_id}").status_code == 404


def test_admin_recipe_validation_and_duplicate_slug(app, client):
    admin = make_admin()
    first = client.post(
        "/api/v1/admin/recipes",
        headers=auth_headers(app, admin),
        json=recipe_payload(slug="stable-admin-recipe"),
    )
    assert first.status_code == 201
    duplicate = client.post(
        "/api/v1/admin/recipes",
        headers=auth_headers(app, admin),
        json=recipe_payload(name="Different Name", slug="stable-admin-recipe"),
    )
    assert duplicate.status_code == 409
    invalid = client.post(
        "/api/v1/admin/recipes",
        headers=auth_headers(app, admin),
        json=recipe_payload(serving_size=0),
    )
    assert invalid.status_code == 400


def test_family_management_prevents_orphaned_recipes(app, client):
    admin = make_admin()
    created = client.post(
        "/api/v1/admin/dish-families",
        headers=auth_headers(app, admin),
        json={"name": "Admin Family", "category": "Curries"},
    )
    assert created.status_code == 201
    family_id = created.get_json()["data"]["family"]["id"]
    duplicate = client.post(
        "/api/v1/admin/dish-families",
        headers=auth_headers(app, admin),
        json={"name": "Admin Family", "category": "Curries"},
    )
    assert duplicate.status_code == 409
    db.session.add(
        Recipe(
            name="Family Recipe",
            category="Curries",
            family_id=family_id,
            serving_size=2,
            steps=["Cook."],
            publication_status="published",
        )
    )
    db.session.commit()
    refused = client.delete(
        f"/api/v1/admin/dish-families/{family_id}",
        headers=auth_headers(app, admin),
    )
    assert refused.status_code == 409


def test_user_suspension_and_final_admin_protection(app, client, sample_user):
    admin = make_admin()
    suspended = client.patch(
        f"/api/v1/admin/users/{sample_user.id}",
        headers=auth_headers(app, admin),
        json={"is_active": False},
    )
    assert suspended.status_code == 200
    denied = client.get(
        "/api/v1/profile", headers=auth_headers(app, sample_user)
    )
    assert denied.status_code == 403
    self_demote = client.patch(
        f"/api/v1/admin/users/{admin.id}",
        headers=auth_headers(app, admin),
        json={"role": "user"},
    )
    assert self_demote.status_code == 409
    self_delete = client.delete(
        "/api/v1/profile", headers=auth_headers(app, admin)
    )
    assert self_delete.status_code == 409


def test_advertisement_moderation_requires_admin_and_paid_order(
    app, client, sample_user
):
    admin = make_admin()
    order = AdvertisingOrder(
        user_id=sample_user.id,
        payment_status="paid",
        review_status="under_review",
    )
    db.session.add(order)
    db.session.commit()
    assert client.patch(
        f"/api/v1/admin/advertisements/{order.id}",
        headers=auth_headers(app, sample_user),
        json={"review_status": "approved"},
    ).status_code == 403
    approved = client.patch(
        f"/api/v1/admin/advertisements/{order.id}",
        headers=auth_headers(app, admin),
        json={"review_status": "approved"},
    )
    assert approved.status_code == 200
    assert order.review_status == "approved"


def test_seeder_does_not_overwrite_admin_managed_recipe(app):
    seed_recipes()
    recipe = Recipe.query.filter_by(slug="chicken-biryani").first()
    assert recipe is not None
    recipe.description = "Admin-owned description"
    recipe.managed_by_admin = True
    db.session.commit()
    seed_recipes()
    db.session.refresh(recipe)
    assert recipe.description == "Admin-owned description"
