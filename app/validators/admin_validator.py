import re
from urllib.parse import urlparse

from app.validators.recipe_validator import (
    validate_recipe_create,
    validate_recipe_update,
)

PUBLICATION_STATUSES = {"draft", "published", "inactive"}
USER_ROLES = {"user", "admin"}
ADVERTISEMENT_REVIEW_STATUSES = {
    "under_review",
    "approved",
    "rejected",
    "active",
    "completed",
}


def _clean_text(value, *, required=False, max_length=None):
    if value is None:
        return (None, "is required") if required else (None, None)
    if not isinstance(value, str):
        return None, "must be a string"
    value = " ".join(value.strip().split())
    if required and not value:
        return None, "is required"
    if max_length and len(value) > max_length:
        return None, f"must not exceed {max_length} characters"
    return value or None, None


def _validate_image_url(value):
    if value in (None, ""):
        return "", None
    if not isinstance(value, str):
        return None, "image must be a URL string."
    value = value.strip()
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None, "image must be an absolute http or https URL."
    if parsed.hostname != "images.unsplash.com":
        return None, "image must use the configured images.unsplash.com host."
    if len(value) > 500:
        return None, "image must not exceed 500 characters."
    return value, None


def _validate_cooking_steps(value):
    if value is None:
        return [], None
    if not isinstance(value, list):
        return None, {"cooking_steps": "cooking_steps must be a list."}

    cleaned = []
    errors = {}
    integer_fields = (
        "duration",
        "minimum_duration",
        "maximum_duration",
        "temperature_min",
        "temperature_max",
    )
    text_fields = (
        "heat_level",
        "visual_cue",
        "colour_stage",
        "texture_cue",
        "aroma_cue",
        "transformation_before",
        "transformation_process",
        "transformation_after",
        "purpose",
        "correction",
        "scientific_explanation",
    )
    list_fields = ("benefits", "warnings", "common_mistakes")

    for index, item in enumerate(value):
        if not isinstance(item, dict):
            errors[f"cooking_steps[{index}]"] = "Each cooking step must be an object."
            continue
        title, title_error = _clean_text(item.get("title"), required=True, max_length=160)
        instruction, instruction_error = _clean_text(
            item.get("instruction"), required=True
        )
        if title_error:
            errors[f"cooking_steps[{index}].title"] = f"title {title_error}."
        if instruction_error:
            errors[f"cooking_steps[{index}].instruction"] = (
                f"instruction {instruction_error}."
            )
        entry = {"title": title, "instruction": instruction}
        for field in integer_fields:
            number = item.get(field)
            if number in (None, ""):
                entry[field] = None
            elif not isinstance(number, int) or isinstance(number, bool) or number < 0:
                errors[f"cooking_steps[{index}].{field}"] = (
                    f"{field} must be a non-negative integer or null."
                )
            else:
                entry[field] = number
        for field in text_fields:
            text, text_error = _clean_text(item.get(field))
            if text_error:
                errors[f"cooking_steps[{index}].{field}"] = f"{field} {text_error}."
            entry[field] = text
        for field in list_fields:
            values = item.get(field) or []
            if not isinstance(values, list) or not all(
                isinstance(part, str) and part.strip() for part in values
            ):
                errors[f"cooking_steps[{index}].{field}"] = (
                    f"{field} must be a list of non-empty strings."
                )
            else:
                entry[field] = [part.strip() for part in values]
        ingredient_names = item.get("ingredient_names") or []
        if not isinstance(ingredient_names, list) or not all(
            isinstance(part, str) and part.strip() for part in ingredient_names
        ):
            errors[f"cooking_steps[{index}].ingredient_names"] = (
                "ingredient_names must be a list of non-empty strings."
            )
        else:
            entry["ingredient_names"] = list(
                dict.fromkeys(part.strip() for part in ingredient_names)
            )
        critical = item.get("critical", False)
        if not isinstance(critical, bool):
            errors[f"cooking_steps[{index}].critical"] = "critical must be a boolean."
        entry["critical"] = bool(critical)
        cleaned.append(entry)

    return (None, errors) if errors else (cleaned, None)


def _reject_duplicate_ingredients(cleaned, errors):
    seen = set()
    for index, ingredient in enumerate(cleaned.get("ingredients") or []):
        normalized = re.sub(r"\s+", " ", ingredient["name"].strip().casefold())
        if len(normalized) > 3 and normalized.endswith("s") and not normalized.endswith("ss"):
            normalized = normalized[:-1]
        if normalized in seen:
            errors[f"ingredients[{index}].name"] = (
                "Duplicate ingredient name in this recipe."
            )
        seen.add(normalized)
        ingredient["name"] = " ".join(ingredient["name"].strip().split())


def validate_admin_recipe(data, *, partial=False):
    cleaned, errors = (
        validate_recipe_update(data) if partial else validate_recipe_create(data)
    )
    errors = dict(errors or {})
    cleaned = dict(cleaned or {})
    if not isinstance(data, dict):
        return None, errors or {"body": "Request body must be valid JSON."}

    if "publication_status" in data or not partial:
        status = data.get("publication_status", "draft")
        if status not in PUBLICATION_STATUSES:
            errors["publication_status"] = (
                "publication_status must be draft, published, or inactive."
            )
        else:
            cleaned["publication_status"] = status

    if "image" in data:
        image, image_error = _validate_image_url(data.get("image"))
        if image_error:
            errors["image"] = image_error
        else:
            cleaned["image"] = image

    if "cooking_steps" in data:
        cooking_steps, cooking_errors = _validate_cooking_steps(
            data.get("cooking_steps")
        )
        if cooking_errors:
            errors.update(cooking_errors)
        else:
            cleaned["cooking_steps"] = cooking_steps

    _reject_duplicate_ingredients(cleaned, errors)
    if partial and cleaned:
        errors.pop("body", None)
    return (None, errors) if errors else (cleaned, None)


def validate_admin_family(data, *, partial=False):
    if not isinstance(data, dict) or (partial and not data):
        return None, {"body": "Request body must be a non-empty JSON object."}
    cleaned = {}
    errors = {}
    fields = (
        ("name", True, 120),
        ("slug", True, 140),
        ("description", False, None),
        ("category", True, 80),
    )
    for field, required, maximum in fields:
        if partial and field not in data:
            continue
        value, error = _clean_text(
            data.get(field), required=required, max_length=maximum
        )
        if error:
            errors[field] = f"{field} {error}."
        else:
            cleaned[field] = value
    if "slug" in cleaned and not re.fullmatch(
        r"[a-z0-9]+(?:-[a-z0-9]+)*", cleaned["slug"] or ""
    ):
        errors["slug"] = "slug must contain lowercase letters, numbers, and hyphens."
    if "image" in data:
        image, image_error = _validate_image_url(data.get("image"))
        if image_error:
            errors["image"] = image_error
        else:
            cleaned["image"] = image
    if "is_active" in data:
        if not isinstance(data["is_active"], bool):
            errors["is_active"] = "is_active must be a boolean."
        else:
            cleaned["is_active"] = data["is_active"]
    elif not partial:
        cleaned["is_active"] = True
    return (None, errors) if errors else (cleaned, None)


def validate_admin_user_update(data):
    if not isinstance(data, dict) or not data:
        return None, {"body": "Request body must be a non-empty JSON object."}
    cleaned = {}
    errors = {}
    if "role" in data:
        if data["role"] not in USER_ROLES:
            errors["role"] = "role must be user or admin."
        else:
            cleaned["role"] = data["role"]
    if "is_active" in data:
        if not isinstance(data["is_active"], bool):
            errors["is_active"] = "is_active must be a boolean."
        else:
            cleaned["is_active"] = data["is_active"]
    if not cleaned and not errors:
        errors["body"] = "Provide role or is_active."
    return (None, errors) if errors else (cleaned, None)
