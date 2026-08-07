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
