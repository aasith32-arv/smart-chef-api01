class QuantityCalculatorService:
    """Reusable service for scaling ingredient quantities based on serving size."""

    UNIT_ALIASES = {
        "g": "g",
        "gram": "g",
        "grams": "g",
        "kg": "kg",
        "kilogram": "kg",
        "kilograms": "kg",
        "ml": "ml",
        "milliliter": "ml",
        "milliliters": "ml",
        "l": "L",
        "liter": "L",
        "liters": "L",
        "litre": "L",
        "litres": "L",
        "tsp": "tsp",
        "teaspoon": "tsp",
        "teaspoons": "tsp",
        "tbsp": "tbsp",
        "tablespoon": "tbsp",
        "tablespoons": "tbsp",
        "cup": "cup",
        "cups": "cup",
        "piece": "piece",
        "pieces": "piece",
        "pcs": "piece",
    }

    @classmethod
    def normalize_unit(cls, unit):
        return cls.UNIT_ALIASES.get(unit.strip().lower(), unit.strip())

    @classmethod
    def format_quantity(cls, quantity, unit):
        """Format scaled quantity with smart unit conversion."""
        unit = cls.normalize_unit(unit)

        if unit == "g" and quantity >= 1000:
            quantity = quantity / 1000
            unit = "kg"
        elif unit == "ml" and quantity >= 1000:
            quantity = quantity / 1000
            unit = "L"

        if unit in ("g", "ml"):
            if quantity >= 10:
                return f"{int(round(quantity))} {unit}"
            return f"{round(quantity, 1)} {unit}"
