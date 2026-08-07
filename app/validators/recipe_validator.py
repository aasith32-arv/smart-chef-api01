def _validate_ingredient(ingredient, index):
    errors = {}
    if not isinstance(ingredient, dict):
        return None, {f"ingredients[{index}]": "Each ingredient must be an object."}

    name = ingredient.get("name")
    if not name or not isinstance(name, str) or not name.strip():
        errors[f"ingredients[{index}].name"] = "name is required."
    else:
        name = name.strip()

    quantity = ingredient.get("quantity")
    if quantity is None:
        errors[f"ingredients[{index}].quantity"] = "quantity is required."
    elif not isinstance(quantity, (int, float)) or isinstance(quantity, bool):
        errors[f"ingredients[{index}].quantity"] = "quantity must be a number."
    elif quantity <= 0:
        errors[f"ingredients[{index}].quantity"] = "quantity must be greater than 0."

    unit = ingredient.get("unit")
    if not unit or not isinstance(unit, str) or not unit.strip():
        errors[f"ingredients[{index}].unit"] = "unit is required."
    else:
        unit = unit.strip()

    if errors:
        return None, errors

    return {"name": name, "quantity": float(quantity), "unit": unit}, None


def _validate_steps(steps):
    if not steps or not isinstance(steps, list):
        return None, {"steps": "steps is required and must be a non-empty list."}
    if not all(isinstance(s, str) and s.strip() for s in steps):
        return None, {"steps": "each step must be a non-empty string."}
    return [s.strip() for s in steps], None


def validate_recipe_create(data):
    errors = {}
    if not data or not isinstance(data, dict):
        return None, {"body": "Request body must be valid JSON."}

    name = data.get("name")
    if not name or not isinstance(name, str) or not name.strip():
        errors["name"] = "name is required."
    else:
        name = name.strip()

    category = data.get("category")
    if not category or not isinstance(category, str) or not category.strip():
        errors["category"] = "category is required."
    else:
        category = category.strip()

    description = data.get("description", "")
    if description is not None and not isinstance(description, str):
        errors["description"] = "description must be a string."
    else:
        description = description.strip() if description else ""

    serving_size = data.get("serving_size")
    if serving_size is None:
        errors["serving_size"] = "serving_size is required."
    elif not isinstance(serving_size, int) or isinstance(serving_size, bool):
        errors["serving_size"] = "serving_size must be a positive integer."
    elif serving_size < 1:
        errors["serving_size"] = "serving_size must be at least 1."

    image = data.get("image", "")
    if image is not None and not isinstance(image, str):
        errors["image"] = "image must be a string."
    else:
        image = image.strip() if image else ""

    ingredients = data.get("ingredients")
    cleaned_ingredients = []
    if not ingredients or not isinstance(ingredients, list):
        errors["ingredients"] = "ingredients is required and must be a non-empty list."
    else:
        for idx, ing in enumerate(ingredients):
            cleaned, ing_errors = _validate_ingredient(ing, idx)
            if ing_errors:
                errors.update(ing_errors)
            elif cleaned:
                cleaned_ingredients.append(cleaned)

    steps, step_errors = _validate_steps(data.get("steps"))
    if step_errors:
        errors.update(step_errors)
