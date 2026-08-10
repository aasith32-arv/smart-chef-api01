from app.cooking_intelligence import CookingPlanService
from app.extensions import db
from app.models import DishFamily, Recipe
from app.seeders import seed_recipes
from app.services import QuantityCalculatorService, RecommendationService


def _seed():
    seed_recipes()


def test_dish_family_listing_and_variety_endpoint(client, app):
    _seed()

    response = client.get("/api/v1/dish-families")
    assert response.status_code == 200
    data = response.get_json()["data"]
    biryani = next(item for item in data["items"] if item["slug"] == "biryani")
    assert data["count"] == 23
    assert biryani["recipe_count"] == 22

    varieties = client.get("/api/v1/dish-families/biryani/recipes?per_page=100")
    assert varieties.status_code == 200
    payload = varieties.get_json()["data"]
    assert payload["family"]["name"] == "Biryani"
    assert payload["meta"]["total"] == 22
    names = {item["name"] for item in payload["items"]}
    assert "Hyderabadi Chicken Biryani" in names
    assert "Dindigul Biryani" in names


def test_family_and_recipe_search_use_discovery_metadata(client, app):
    _seed()

    family_search = client.get("/api/v1/dish-families?search=Hyderabadi")
    slugs = {item["slug"] for item in family_search.get_json()["data"]["items"]}
    assert "biryani" in slugs

    recipe_search = client.get("/api/v1/recipes?search=Jaffna&per_page=100")
    items = recipe_search.get_json()["data"]["items"]
    assert items
    assert all(
        "jaffna"
        in " ".join(
            str(value)
            for value in (
                item["name"],
                item["region"],
                item["cuisine"],
                item["tags"],
            )
        ).casefold()
        for item in items
    )

    filtered = client.get(
        "/api/v1/recipes?family=biryani&protein=Chicken&difficulty=Advanced&per_page=100"
    )
    filtered_items = filtered.get_json()["data"]["items"]
    assert filtered_items
    assert all(item["family"]["slug"] == "biryani" for item in filtered_items)
    assert all(item["protein"] == "Chicken" for item in filtered_items)


def test_existing_recipe_without_family_metadata_remains_visible(client, sample_recipe):
    response = client.get(f"/api/v1/recipes/{sample_recipe.id}")
    assert response.status_code == 200
    recipe = response.get_json()["data"]["recipe"]
    assert recipe["name"] == "Test Curry"
    assert recipe["family_id"] is None
    assert recipe["family"] is None
    assert recipe["tags"] == []


def test_variety_scales_to_fifty_people_and_builds_cooking_plan(app):
    _seed()
    recipe = Recipe.query.filter_by(name="Dindigul Biryani").one()

    quantities, error = QuantityCalculatorService.calculate_for_recipe(recipe, 50)
    assert error is None
    assert quantities["Seeraga samba rice"] == "6.2 kg"
    assert quantities["Chicken"] == "9.4 kg"

    plan, errors = CookingPlanService.build(recipe, {"servings": 50})
    assert errors is None
    assert plan["recipe"]["id"] == recipe.id
    assert plan["servings"] == 50
    assert plan["source"] == "rule-based"
    assert any("absorption" in step["instruction"].casefold() for step in plan["steps"])


def test_catalog_varieties_remain_compatible_with_pantry_recommendations(app):
    _seed()
    recipes = Recipe.query.filter(Recipe.family.has(slug="biryani")).all()
    pantry = ["basmati rice", "chicken", "onion", "ginger garlic paste", "yogurt"]

    results = RecommendationService.recommend(recipes, pantry, include_partial=True)
    names = {item["recipe"]["name"] for item in results}
    assert "Hyderabadi Chicken Biryani" in names
    assert all(item["match_percentage"] > 0 for item in results)


def test_catalog_seeding_is_idempotent_and_has_no_duplicates(app):
    first = seed_recipes()
    first_recipe_count = Recipe.query.count()
    first_family_count = DishFamily.query.count()

    second = seed_recipes()
    assert first["recipes_created"] == 189
    assert first_recipe_count == 189
    assert first_family_count == 23
    assert second["recipes_created"] == 0
    assert second["recipes_enriched"] == 0
    assert Recipe.query.count() == first_recipe_count
    assert DishFamily.query.count() == first_family_count

    names = [name.casefold() for (name,) in db.session.query(Recipe.name).all()]
    slugs = [slug for (slug,) in db.session.query(Recipe.slug).filter(Recipe.slug.is_not(None)).all()]
    assert len(names) == len(set(names))
    assert len(slugs) == len(set(slugs))
