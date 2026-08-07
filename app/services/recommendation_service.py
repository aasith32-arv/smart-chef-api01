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
