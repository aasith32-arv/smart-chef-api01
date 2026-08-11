import pytest

from app.ai import CookingRecommendationService
from app.extensions import db
from app.models import DishFamily, Ingredient, Recipe


@pytest.mark.parametrize(
    "ingredient",
    [
        "Chicken",
        "Onion",
        "Ginger garlic paste",
        "Yogurt",
        "Ghee",
        "Mint leaves",
        "Coriander leaves",
        "Salt",
        "Biryani masala",
        "Lemon juice",
        "Saffron milk",
    ],
)
def test_chicken_dum_biryani_ingredients_have_verified_substitutions(ingredient):
    result = CookingRecommendationService.substitute(ingredient)

    assert result["options"], f"Expected substitution coverage for {ingredient}"
    assert result["no_substitute_reason"] is None


def test_get_cooking_plan_with_scaled_servings(client, sample_recipe):
    sample_recipe.steps = [
        "Heat oil.",
        "Saute onion for 5 minutes.",
        "Add chicken and simmer for 20 minutes.",
    ]

    response = client.get(
        f"/api/v1/recipes/{sample_recipe.id}/cooking-plan?servings=8"
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert body["data"]["servings"] == 8
    assert len(body["data"]["steps"]) == 3


def test_personalized_cooking_plan_rejects_invalid_preferences(client, sample_recipe):
    response = client.post(
        f"/api/v1/recipes/{sample_recipe.id}/cooking-plan",
        json={"servings": 0, "spice_level": "extreme"},
    )

    assert response.status_code == 400
    assert "servings" in response.get_json()["errors"]


def test_cooking_plan_missing_recipe(client):
    response = client.get("/api/v1/recipes/999999/cooking-plan")

    assert response.status_code == 404


def test_troubleshooting_route(client):
    response = client.post(
        "/api/v1/cooking/troubleshoot", json={"problem": "too watery"}
    )

    assert response.status_code == 200
    result = response.get_json()["data"]
    assert result["probable_cause"]
    assert result["immediate_action"]
    assert result["recovery_option"]
    assert result["prevention_tip"]


def test_substitution_route_is_contextual(client, sample_recipe):
    response = client.post(
        "/api/v1/cooking/substitute",
        json={"ingredient": "yogurt", "recipe_id": sample_recipe.id},
    )

    assert response.status_code == 200
    result = response.get_json()["data"]
    assert result["options"][0]["how_much"]
    assert result["options"][0]["what_changes"]


def test_biryani_substitution_uses_trusted_recipe_and_scaled_ingredient(app, client):
    family = DishFamily(
        name="Biryani",
        slug="biryani",
        description="Layered rice dishes",
        category="Rice Dishes",
        is_active=True,
    )
    recipe = Recipe(
        name="Hyderabadi Chicken Biryani",
        slug="hyderabadi-chicken-biryani-test",
        category="Rice Dishes",
        family=family,
        cuisine="Indian",
        region="Hyderabad",
        serving_size=4,
        steps=["Parboil the rice and layer for dum."],
    )
    rice = Ingredient(name="Basmati rice", quantity=500, unit="g")
    recipe.ingredients.append(rice)
    db.session.add(recipe)
    db.session.commit()

    response = client.post(
        "/api/v1/cooking/substitute",
        json={
            "ingredient": "untrusted name is ignored",
            "ingredient_id": rice.id,
            "recipe_id": recipe.id,
            "servings": 50,
        },
    )

    assert response.status_code == 200
    result = response.get_json()["data"]
    assert result["ingredient"] == "Basmati rice"
    assert result["original_display"] == "6.2 kg"
    assert result["source"] == "contextual-rule-based"
    assert len(result["options"]) == 3
    assert result["options"][0]["suitability"] == "Best Match"
    assert result["options"][0]["display_quantity"] == "6.2 kg"


def test_known_recipe_returns_verified_core_ingredient_substitutes(client, sample_recipe):
    chicken = next(item for item in sample_recipe.ingredients if item.name == "Chicken")
    response = client.post(
        "/api/v1/cooking/substitute",
        json={
            "ingredient": chicken.name,
            "ingredient_id": chicken.id,
            "recipe_id": sample_recipe.id,
            "servings": 8,
            "use_ai": True,
        },
    )

    assert response.status_code == 200
    result = response.get_json()["data"]
    assert result["options"]
    assert result["options"][0]["substitution"] == "boneless turkey thigh"
    assert result["no_substitute_reason"] is None
    assert result["original_display"] == "1 kg"


def test_recipe_mutation_still_requires_authentication(client):
    response = client.post("/api/v1/recipes", json={})

    assert response.status_code == 401
