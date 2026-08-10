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

    DEBUG = _env_bool("FLASK_DEBUG", default=False)

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

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "15"))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "30"))
    )

    # SQLite by default; switch to MySQL by setting DATABASE_URL or DB_* vars
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        DB_USER = os.getenv("DB_USER", "root")
        DB_PASSWORD = os.getenv("DB_PASSWORD", "")
        DB_HOST = os.getenv("DB_HOST", "localhost")
        DB_NAME = os.getenv("DB_NAME", "aichef_db1")
        DB_PORT = os.getenv("DB_PORT", "3306")

        if os.getenv("USE_MYSQL", "false").lower() == "true":
            SQLALCHEMY_DATABASE_URI = (
                f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
            )
        else:
            basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
            db_path = os.path.join(basedir, "instance", "aichef.db")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", "10"))
    MAX_PAGE_SIZE = int(os.getenv("MAX_PAGE_SIZE", "50"))

    # In-memory rate-limit storage is fine for single-process local/dev.
    # Use Redis (e.g. redis://localhost:6379) for multi-worker production.
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_HEADERS_ENABLED = True

    STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "").strip()
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "").strip()
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
    STRIPE_SUBSCRIPTION_PRICE_ID = os.getenv("STRIPE_SUBSCRIPTION_PRICE_ID", "").strip()
    STRIPE_ADVERTISING_PRICE_ID = os.getenv("STRIPE_ADVERTISING_PRICE_ID", "").strip()
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
