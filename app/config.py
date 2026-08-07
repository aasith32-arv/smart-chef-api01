import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    """Application configuration loaded from environment variables."""

    # Development fallbacks are deliberately long enough for HS256. Production
    # deployments should always set unique values through environment variables.
    SECRET_KEY = os.getenv(
        "SECRET_KEY", "development-secret-key-change-me-please-use-an-env-variable"
    )
    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY", "development-jwt-secret-key-change-me-please-use-an-env-variable"
    )

    # Dual location: cookies for the web app; Bearer headers still work for Swagger /
    # API clients that cannot store cookies.
    JWT_TOKEN_LOCATION = ["headers", "cookies"]
    JWT_COOKIE_SECURE = _env_bool("JWT_COOKIE_SECURE", default=False)
    JWT_COOKIE_SAMESITE = os.getenv("JWT_COOKIE_SAMESITE", "Lax")
    JWT_COOKIE_CSRF_PROTECT = _env_bool("JWT_COOKIE_CSRF_PROTECT", default=True)
    JWT_ACCESS_COOKIE_PATH = "/"
    JWT_REFRESH_COOKIE_PATH = "/"
    JWT_COOKIE_DOMAIN = os.getenv("JWT_COOKIE_DOMAIN") or None

