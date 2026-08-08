class PersonalizationEngine:
    SPICE_FACTORS = {"mild": 0.7, "medium": 1.0, "hot": 1.25}
    OIL_FACTORS = {"low": 0.75, "standard": 1.0}
    SALT_FACTORS = {"low": 0.75, "standard": 1.0}
    RESTRICTION_CONFLICTS = {
        "vegetarian": ("chicken", "fish", "beef", "pork", "lamb"),
        "vegan": ("chicken", "fish", "beef", "pork", "lamb", "egg", "yogurt", "milk"),
        "dairy-free": ("yogurt", "milk", "butter", "ghee", "cream"),
        "gluten-free": ("roti", "flour", "soy sauce"),
    }

    @classmethod
    def normalize(cls, payload, default_servings):
        data = payload if hasattr(payload, "get") else {}
        errors = {}
        try:
            servings = int(data.get("servings", default_servings))
            if not 1 <= servings <= 100:
                errors["servings"] = "servings must be between 1 and 100."
        except (TypeError, ValueError):
            servings = default_servings
            errors["servings"] = "servings must be an integer."

        preferences = {
            "servings": servings,
            "spice_level": str(data.get("spice_level", "medium")).casefold(),
            "oil_level": str(data.get("oil_level", "standard")).casefold(),
            "salt_preference": str(data.get("salt_preference", "standard")).casefold(),
            "dietary_restrictions": cls._string_list(data.get("dietary_restrictions", [])),
            "cooking_method": str(data.get("cooking_method", "stovetop")).strip(),
            "cookware": str(data.get("cookware", "standard pan")).strip(),
            "available_ingredients": cls._string_list(data.get("available_ingredients", [])),
            "preferred_texture": str(data.get("preferred_texture", "as written")).strip(),
            "beginner_mode": cls._bool(data.get("beginner_mode", True)),
            "science_mode": cls._bool(data.get("science_mode", False)),
        }
        for key, choices in (
            ("spice_level", cls.SPICE_FACTORS),
            ("oil_level", cls.OIL_FACTORS),
            ("salt_preference", cls.SALT_FACTORS),
        ):
            if preferences[key] not in choices:
                errors[key] = f"{key} must be one of: {', '.join(choices)}."
        return preferences, errors

    @classmethod
    def scaled_ingredients(cls, recipe, preferences):
        factor = preferences["servings"] / max(recipe.serving_size, 1)
        items = []
        for ingredient in recipe.ingredients:
            adjustment = 1.0
            name = ingredient.name.casefold()
            if any(word in name for word in ("chili", "chilli", "masala", "pepper")):
                adjustment *= cls.SPICE_FACTORS[preferences["spice_level"]]
            if any(word in name for word in ("oil", "ghee", "butter")):
                adjustment *= cls.OIL_FACTORS[preferences["oil_level"]]
            if "salt" in name:
                adjustment *= cls.SALT_FACTORS[preferences["salt_preference"]]
            quantity = cls._round(ingredient.quantity * factor * adjustment)
            items.append(
                {
                    "id": ingredient.id,
                    "name": ingredient.name,
                    "quantity": quantity,
                    "unit": ingredient.unit,
                    "display": cls._display(quantity, ingredient.unit),
                    "adjusted": adjustment != 1.0,
                }
            )
        return items

    @classmethod
    def notes(cls, recipe, preferences, scaled_ingredients):
        names = [item["name"].casefold() for item in scaled_ingredients]
        notes = []
        restrictions = [item.casefold() for item in preferences["dietary_restrictions"]]
        for restriction in restrictions:
            conflicts = cls.RESTRICTION_CONFLICTS.get(restriction, ())
            matched = [name for name in names if any(word in name for word in conflicts)]
            if matched:
                notes.append(
                    {
                        "level": "warning",
                        "message": (
                            f"This stored recipe conflicts with {restriction}: "
                            f"{', '.join(sorted(set(matched)))}. Use a validated substitution "
                            "before cooking; the system has not silently replaced it."
                        ),
                    }
                )
        available = [item.casefold() for item in preferences["available_ingredients"]]
        if available:
            missing = [
                item["name"]
                for item in scaled_ingredients
                if item["name"].casefold() not in available
            ]
            if missing:
                notes.append(
                    {
                        "level": "info",
                        "message": "Not marked available: " + ", ".join(missing),
                    }
                )
        if preferences["cookware"].casefold() != "standard pan":
            notes.append(
                {
                    "level": "info",
                    "message": (
                        f"Using {preferences['cookware']}: monitor heat and moisture closely; "
                        "timing ranges may shift."
                    ),
                }
            )
        if preferences["preferred_texture"].casefold() != "as written":
            notes.append(
                {
                    "level": "info",
                    "message": (
                        f"Preferred texture: {preferences['preferred_texture']}. Use observable "
                        "cues and adjust only within food-safety limits."
                    ),
                }
            )
        return notes

    @staticmethod
    def beginner_instruction(heat_level):
        messages = {
            "LOW": "Keep the flame low; look for small, gentle bubbles rather than a hard boil.",
            "LOW-MEDIUM": "Use a low to medium flame and adjust if the pan starts smoking.",
            "MEDIUM": "Use a medium flame; the food should sizzle gently, not scorch.",
            "MEDIUM-HIGH": "Use medium-high heat and stay close so you can stir or turn promptly.",
            "HIGH": "Use high heat only for this short stage and keep the food moving.",
            "HIGH → MEDIUM": "Bring it to a boil on high, then lower the flame to keep it controlled.",
            "OFF": "Turn the heat off for this stage.",
        }
        return messages.get(heat_level, "Adjust the flame using the visual cues in this step.")

    @staticmethod
    def _string_list(value):
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()]

    @staticmethod
    def _bool(value):
        if isinstance(value, bool):
            return value
        return str(value).casefold() in {"1", "true", "yes", "on"}

    @staticmethod
    def _round(value):
        if value >= 100:
            return round(value)
        if value >= 10:
            return round(value, 1)
        return round(value, 2)

    @classmethod
    def _display(cls, quantity, unit):
        if unit == "g" and quantity >= 1000:
            return f"{cls._round(quantity / 1000):g} kg"
        if unit == "ml" and quantity >= 1000:
            return f"{cls._round(quantity / 1000):g} L"
        if unit in {"piece", "pcs"}:
            amount = max(1, round(quantity))
            return f"{amount} {'piece' if amount == 1 else 'pieces'}"
        return f"{quantity:g} {unit}"
