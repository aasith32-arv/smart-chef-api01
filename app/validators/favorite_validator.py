def validate_favorite_create(data):
    errors = {}
    if not data or not isinstance(data, dict):
        return None, {"body": "Request body must be valid JSON."}

    recipe_id = data.get("recipe_id")
    if recipe_id is None:
        errors["recipe_id"] = "recipe_id is required."
    elif not isinstance(recipe_id, int) or isinstance(recipe_id, bool):
        errors["recipe_id"] = "recipe_id must be a positive integer."
    elif recipe_id < 1:
        errors["recipe_id"] = "recipe_id must be a positive integer."

    if errors:
        return None, errors

    return {"recipe_id": recipe_id}, None
