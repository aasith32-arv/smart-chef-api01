from app.extensions import db
from app.models import Ingredient, Recipe
from app.services.recommendation_service import RecommendationService


def _make_recipe(name, ingredient_names):
    recipe = Recipe(
        name=name,
        category="Test",
        description=None,
        serving_size=2,
        steps=["Cook"],
        image=None,
    )
    db.session.add(recipe)
    db.session.flush()
    for item in ingredient_names:
        db.session.add(
            Ingredient(recipe_id=recipe.id, name=item, quantity=1, unit="piece")
        )
    db.session.commit()
    return recipe


class TestRecommendationService:
    def test_full_match_only_by_default(self, app):
        rice = _make_recipe("Egg Fried Rice", ["Rice", "Egg", "Onion"])
        curry = _make_recipe("Chicken Curry", ["Chicken", "Onion", "Spice"])
        available = ["rice", "egg", "onion"]

        results = RecommendationService.recommend(
            [rice, curry], available, include_partial=False
        )
        assert len(results) == 1
        assert results[0]["recipe"]["name"] == "Egg Fried Rice"
        assert results[0]["match_percentage"] == 100.0
        assert results[0]["missing_ingredients"] == []

    def test_partial_match_mode(self, app):
        rice = _make_recipe("Egg Fried Rice", ["Rice", "Egg", "Onion"])
        curry = _make_recipe("Chicken Curry", ["Chicken", "Onion", "Spice"])
        available = ["onion", "chicken"]

        results = RecommendationService.recommend(
            [rice, curry], available, include_partial=True
        )
        assert len(results) == 2
        assert results[0]["recipe"]["name"] == "Chicken Curry"
        assert results[0]["match_percentage"] == 66.7
        assert "Spice" in results[0]["missing_ingredients"]

        rice_result = next(r for r in results if r["recipe"]["name"] == "Egg Fried Rice")
        assert rice_result["match_percentage"] == 33.3

    def test_no_match_when_empty_pantry(self, app):
        recipe = _make_recipe("Dhal", ["Lentils", "Onion"])
        assert RecommendationService.recommend([recipe], []) == []

    def test_case_insensitive_matching(self, app):
        recipe = _make_recipe("Onion Dish", ["Onion"])
        assert RecommendationService.can_prepare_recipe(recipe, [" ONION "]) is True

    def test_empty_recipe_ingredients_not_matchable(self, app):
        recipe = Recipe(
            name="Empty",
            category="Test",
            description=None,
            serving_size=1,
            steps=[],
            image=None,
        )
        db.session.add(recipe)
        db.session.commit()
        assert RecommendationService.can_prepare_recipe(recipe, ["anything"]) is False
        assert RecommendationService.match_score(recipe, ["anything"]) == 0.0
