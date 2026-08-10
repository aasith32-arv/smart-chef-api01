import re

OPTIONAL_TEXT_FIELDS = (
    "cuisine",
    "region",
    "protein",
    "diet_type",
    "difficulty",
    "spice_level",
)


def _validate_optional_metadata(data, cleaned, errors, *, partial):
    if "slug" in data:
        slug = data.get("slug")
        if slug in (None, ""):
            cleaned["slug"] = None
        elif not isinstance(slug, str) or not re.fullmatch(
            r"[a-z0-9]+(?:-[a-z0-9]+)*", slug.strip()
        ):
            errors["slug"] = "slug must contain lowercase letters, numbers, and hyphens."
        else:
            cleaned["slug"] = slug.strip()

    if "family_id" in data:
        family_id = data.get("family_id")
        if family_id is None:
            cleaned["family_id"] = None
        elif not isinstance(family_id, int) or isinstance(family_id, bool) or family_id < 1:
            errors["family_id"] = "family_id must be a positive integer or null."
        else:
            cleaned["family_id"] = family_id

    for field in OPTIONAL_TEXT_FIELDS:
        if field not in data:
            continue
        value = data.get(field)
        if value in (None, ""):
            cleaned[field] = None
        elif not isinstance(value, str):
            errors[field] = f"{field} must be a string or null."
        else:
            cleaned[field] = value.strip()

    for field in ("prep_time", "cook_time"):
        if field not in data:
            continue
        value = data.get(field)
        if value is None:
            cleaned[field] = None
        elif not isinstance(value, int) or isinstance(value, bool) or value < 0:
            errors[field] = f"{field} must be a non-negative integer or null."
        else:
            cleaned[field] = value

    if "tags" in data:
        tags = data.get("tags")
        if tags is None:
            cleaned["tags"] = []
        elif not isinstance(tags, list) or not all(
            isinstance(tag, str) and tag.strip() for tag in tags
        ):
            errors["tags"] = "tags must be a list of non-empty strings."
        else:
            cleaned["tags"] = list(dict.fromkeys(tag.strip().lower() for tag in tags))

    if not partial:
        cleaned.setdefault("tags", [])


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

    cleaned = {
        "name": name,
        "category": category,
        "description": description,
        "serving_size": serving_size,
        "image": image,
        "ingredients": cleaned_ingredients,
        "steps": steps,
    }
    _validate_optional_metadata(data, cleaned, errors, partial=False)

    if errors:
        return None, errors
    return cleaned, None


def validate_recipe_update(data):
    errors = {}
    if not data or not isinstance(data, dict):
        return None, {"body": "Request body must be valid JSON."}

    if not data:
        return None, {"body": "At least one field must be provided for update."}

    cleaned = {}

    if "name" in data:
        name = data.get("name")
        if not name or not isinstance(name, str) or not name.strip():
            errors["name"] = "name must be a non-empty string."
        else:
            cleaned["name"] = name.strip()

    if "category" in data:
        category = data.get("category")
        if not category or not isinstance(category, str) or not category.strip():
            errors["category"] = "category must be a non-empty string."
        else:
            cleaned["category"] = category.strip()

    if "description" in data:
        description = data.get("description")
        if description is not None and not isinstance(description, str):
            errors["description"] = "description must be a string."
        else:
            cleaned["description"] = description.strip() if description else ""

    if "serving_size" in data:
        serving_size = data.get("serving_size")
        if not isinstance(serving_size, int) or isinstance(serving_size, bool):
            errors["serving_size"] = "serving_size must be a positive integer."
        elif serving_size < 1:
            errors["serving_size"] = "serving_size must be at least 1."
        else:
            cleaned["serving_size"] = serving_size

    if "image" in data:
        image = data.get("image")
        if image is not None and not isinstance(image, str):
            errors["image"] = "image must be a string."
        else:
            cleaned["image"] = image.strip() if image else ""

    if "ingredients" in data:
        ingredients = data.get("ingredients")
        cleaned_ingredients = []
        if not ingredients or not isinstance(ingredients, list):
            errors["ingredients"] = "ingredients must be a non-empty list."
        else:
            for idx, ing in enumerate(ingredients):
                cleaned_ing, ing_errors = _validate_ingredient(ing, idx)
                if ing_errors:
                    errors.update(ing_errors)
                elif cleaned_ing:
                    cleaned_ingredients.append(cleaned_ing)
            if not errors:
                cleaned["ingredients"] = cleaned_ingredients

    if "steps" in data:
        steps, step_errors = _validate_steps(data.get("steps"))
        if step_errors:
            errors.update(step_errors)
        else:
            cleaned["steps"] = steps

    _validate_optional_metadata(data, cleaned, errors, partial=True)

    if errors:
        return None, errors

    if not cleaned:
        return None, {"body": "At least one valid field must be provided for update."}

    return cleaned, None
