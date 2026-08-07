class RecommendationService:
    """Service for recommending recipes based on available ingredients."""

    @staticmethod
    def _normalize_name(name):
        return name.strip().lower()

    @classmethod
    def can_prepare_recipe(cls, recipe, available_ingredients):
        """Check if all recipe ingredients are covered by available ingredients."""
        available = {cls._normalize_name(i) for i in available_ingredients}
        required = [cls._normalize_name(ing.name) for ing in recipe.ingredients]

        if not required:
            return False

        return all(req in available for req in required)

    @classmethod
    def match_score(cls, recipe, available_ingredients):
        """Return match percentage for partial ranking."""
        available = {cls._normalize_name(i) for i in available_ingredients}
        required = [cls._normalize_name(ing.name) for ing in recipe.ingredients]

        if not required:
            return 0.0

        matched = sum(1 for req in required if req in available)
        return matched / len(required)

    @classmethod
    def recommend(cls, recipes, available_ingredients, include_partial=False):
        """
        Return recipes that can be prepared with available ingredients.
        By default returns only fully matchable recipes.
        """
        results = []

        for recipe in recipes:
            if cls.can_prepare_recipe(recipe, available_ingredients):
                results.append(
                    {
                        "recipe": recipe.to_dict(),
                        "match_percentage": 100.0,
                        "missing_ingredients": [],
                    }
                )
            elif include_partial:
                score = cls.match_score(recipe, available_ingredients)
                if score > 0:
                    available = {cls._normalize_name(i) for i in available_ingredients}
                    missing = [
                        ing.name
                        for ing in recipe.ingredients
                        if cls._normalize_name(ing.name) not in available
                    ]
                    results.append(
                        {
                            "recipe": recipe.to_dict(),
                            "match_percentage": round(score * 100, 1),
                            "missing_ingredients": missing,
                        }
                    )

        results.sort(key=lambda x: (-x["match_percentage"], x["recipe"]["name"]))
        return results
