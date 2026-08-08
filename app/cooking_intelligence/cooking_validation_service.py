class CookingValidationService:
    ALLOWED_HEAT_LEVELS = {
        "OFF",
        "LOW",
        "LOW-MEDIUM",
        "MEDIUM",
        "MEDIUM-HIGH",
        "HIGH",
        "HIGH → MEDIUM",
        "OVEN",
    }

    @classmethod
    def validate_plan(cls, plan, recipe=None):
        errors = []
        if not isinstance(plan, dict):
            return ["Cooking plan must be an object."]
        steps = plan.get("steps")
        ingredients = plan.get("ingredients")
        if not isinstance(steps, list) or not steps:
            errors.append("Cooking plan requires at least one step.")
        if not isinstance(ingredients, list) or not ingredients:
            errors.append("Cooking plan requires ingredients.")
        if errors:
            return errors

        recipe_ids = {item.id for item in recipe.ingredients} if recipe else set()
        for index, step in enumerate(steps, start=1):
            if step.get("step_number") != index:
                errors.append("Step numbers must be sequential and start at 1.")
            if not str(step.get("instruction") or "").strip():
                errors.append(f"Step {index} requires an instruction.")
            timing = step.get("timing") or {}
            minimum = timing.get("minimum_minutes")
            maximum = timing.get("maximum_minutes")
            if not all(isinstance(value, int) and value >= 0 for value in (minimum, maximum)):
                errors.append(f"Step {index} has invalid duration values.")
            elif minimum > maximum:
                errors.append(f"Step {index} minimum duration exceeds maximum duration.")
            temperature = step.get("temperature") or {}
            low = temperature.get("minimum_c")
            high = temperature.get("maximum_c")
            if low is not None or high is not None:
                if not all(isinstance(value, int) and 0 <= value <= 300 for value in (low, high)):
                    errors.append(f"Step {index} has an invalid temperature range.")
                elif low > high:
                    errors.append(f"Step {index} minimum temperature exceeds maximum.")
            heat = temperature.get("heat_level")
            if heat not in cls.ALLOWED_HEAT_LEVELS:
                errors.append(f"Step {index} has an invalid heat level.")
            for addition in step.get("ingredients", []):
                ingredient_id = addition.get("id")
                if recipe and ingredient_id not in recipe_ids:
                    errors.append(f"Step {index} references an ingredient outside the recipe.")
                if not isinstance(addition.get("quantity"), (int, float)):
                    errors.append(f"Step {index} has an invalid ingredient quantity.")
                if not str(addition.get("unit") or "").strip():
                    errors.append(f"Step {index} has an invalid ingredient unit.")
        return errors

    @staticmethod
    def validate_ai_payload(payload, required_keys):
        if not isinstance(payload, dict):
            return False
        return all(key in payload and payload[key] not in (None, "", []) for key in required_keys)
