def _require_string(data, field, min_len=1, max_len=255):
    value = data.get(field)
    if value is None or not isinstance(value, str):
        return None, f"{field} is required and must be a string."
    value = value.strip()
    if len(value) < min_len:
        return None, f"{field} must be at least {min_len} characters."
    if len(value) > max_len:
        return None, f"{field} must not exceed {max_len} characters."
    return value, None


def validate_register(data):
    errors = {}
    if not data or not isinstance(data, dict):
        return None, {"body": "Request body must be valid JSON."}

    username, err = _require_string(data, "username", min_len=3, max_len=80)
    if err:
        errors["username"] = err

    email, err = _require_string(data, "email", min_len=5, max_len=120)
    if err:
        errors["email"] = err
    elif "@" not in email:
        errors["email"] = "email must be a valid email address."

    password = data.get("password")
    if not password or not isinstance(password, str):
        errors["password"] = "password is required and must be a string."
    elif len(password) < 6:
        errors["password"] = "password must be at least 6 characters."

    full_name = data.get("full_name", "").strip() if data.get("full_name") else None

    if errors:
        return None, errors

    return {
        "username": username,
        "email": email.lower(),
        "password": password,
        "full_name": full_name,
    }, None


def validate_login(data):
    errors = {}
    if not data or not isinstance(data, dict):
        return None, {"body": "Request body must be valid JSON."}

    email, err = _require_string(data, "email", min_len=5, max_len=120)
    if err:
        errors["email"] = err

    password = data.get("password")
    if not password or not isinstance(password, str):
