def validate_recommend(data):
    errors = {}
    if not data or not isinstance(data, dict):
        return None, {"body": "Request body must be valid JSON."}

    ingredients = data.get("ingredients")
    if not ingredients or not isinstance(ingredients, list):
        errors["ingredients"] = "ingredients is required and must be a non-empty list."
    elif not all(isinstance(i, str) and i.strip() for i in ingredients):
        errors["ingredients"] = "each ingredient must be a non-empty string."
    else:
        ingredients = [i.strip().lower() for i in ingredients]

    if errors:
        return None, errors

    return {"ingredients": ingredients}, None
