import pytest

from app.services.calculator_service import QuantityCalculatorService


class TestNormalizeAndFormat:
    def test_normalize_unit_aliases(self):
        assert QuantityCalculatorService.normalize_unit("Grams") == "g"
        assert QuantityCalculatorService.normalize_unit("litres") == "L"
        assert QuantityCalculatorService.normalize_unit("pcs") == "piece"

    def test_format_converts_grams_to_kg(self):
        assert QuantityCalculatorService.format_quantity(1500, "g") == "1.5 kg"

    def test_format_converts_ml_to_liters(self):
        assert QuantityCalculatorService.format_quantity(2000, "ml") == "2 L"

    def test_format_piece_pluralization(self):
        assert QuantityCalculatorService.format_quantity(1, "piece") == "1 piece"
        assert QuantityCalculatorService.format_quantity(3.2, "pcs") == "3 pieces"


class TestScaleFactor:
    def test_basic_scale_factor(self):
        assert QuantityCalculatorService.calculate_scale_factor(8, 4) == 2.0

    def test_zero_serving_size_raises(self):
        with pytest.raises(ValueError, match="serving_size"):
            QuantityCalculatorService.calculate_scale_factor(4, 0)

    def test_zero_guests_scales_to_zero(self):
        # Service-layer allows 0; HTTP validators may reject it separately.
        factor = QuantityCalculatorService.calculate_scale_factor(0, 4)
        assert factor == 0.0

    def test_huge_guest_count(self):
        factor = QuantityCalculatorService.calculate_scale_factor(10_000, 4)
        assert factor == 2500.0


class TestScaleIngredients:
    def test_scales_dict_ingredients(self):
        ingredients = [
            {"name": "Rice", "quantity": 200, "unit": "g"},
            {"name": "Salt", "quantity": 1, "unit": "tsp"},
        ]
        scaled = QuantityCalculatorService.scale_ingredients(ingredients, 8, 4)
        assert scaled["Rice"] == "400 g"
        assert scaled["Salt"] == "2 tsp"

    def test_zero_people_zeros_out_quantities(self):
        ingredients = [{"name": "Oil", "quantity": 50, "unit": "ml"}]
        scaled = QuantityCalculatorService.scale_ingredients(ingredients, 0, 4)
        assert scaled["Oil"].startswith("0")


class TestCalculateForRecipe:
    def test_missing_ingredients_returns_error(self, app, sample_recipe):
        sample_recipe.ingredients = []
        quantities, error = QuantityCalculatorService.calculate_for_recipe(
            sample_recipe, 4
        )
        assert quantities == {}
        assert error == "Recipe has no ingredients defined."

    def test_scales_orm_ingredients(self, app, sample_recipe):
        quantities, error = QuantityCalculatorService.calculate_for_recipe(
            sample_recipe, 8
        )
        assert error is None
        assert quantities["Chicken"] == "1 kg"
        assert quantities["Onion"] == "4 pieces"
        assert quantities["Oil"] == "60 ml"
