def validate_calculate(data):
    errors = {}
    if not data or not isinstance(data, dict):
        return None, {"body": "Request body must be valid JSON."}

    recipe = data.get("recipe")
    if not recipe or not isinstance(recipe, str) or not recipe.strip():
        errors["recipe"] = "recipe is required and must be a non-empty string."
    else:
        recipe = recipe.strip()

    people = data.get("people")
    if people is None:
        errors["people"] = "people is required."
    elif not isinstance(people, int) or isinstance(people, bool):
        errors["people"] = "people must be a positive integer."
    elif people < 1:
        errors["people"] = "people must be at least 1."

    if errors:
        return None, errors

    return {"recipe": recipe, "people": people}, None
