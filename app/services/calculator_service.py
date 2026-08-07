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

        if unit in ("kg", "L", "tsp", "tbsp"):
            val = round(quantity, 1)
            if val == int(val):
                return f"{int(val)} {unit}"
            return f"{val} {unit}"

        if unit == "piece":
            count = int(round(quantity))
            label = "pieces" if count != 1 else "piece"
            return f"{count} {label}"

        val = round(quantity, 1)
        if val == int(val):
            return f"{int(val)} {unit}"
        return f"{val} {unit}"

    @classmethod
    def calculate_scale_factor(cls, target_people, serving_size):
        if serving_size <= 0:
            raise ValueError("serving_size must be greater than zero")
        return target_people / serving_size

    @classmethod
    def scale_ingredients(cls, ingredients, target_people, serving_size):
        """Scale a list of ingredient dicts for the given number of people."""
        scale_factor = cls.calculate_scale_factor(target_people, serving_size)
        scaled = {}

        for ingredient in ingredients:
            name = ingredient["name"] if isinstance(ingredient, dict) else ingredient.name
            quantity = (
                ingredient["quantity"] if isinstance(ingredient, dict) else ingredient.quantity
            )
            unit = ingredient["unit"] if isinstance(ingredient, dict) else ingredient.unit

            scaled_qty = quantity * scale_factor
            scaled[name] = cls.format_quantity(scaled_qty, unit)

        return scaled

    @classmethod
    def calculate_for_recipe(cls, recipe, people):
        """Calculate scaled ingredient quantities for a recipe."""
        if not recipe.ingredients:
            return {}, "Recipe has no ingredients defined."

        return (
            cls.scale_ingredients(recipe.ingredients, people, recipe.serving_size),
            None,
        )
