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
