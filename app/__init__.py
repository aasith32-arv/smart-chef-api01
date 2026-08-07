import logging
import os
import time

from flasgger import Swagger
from flask import Flask, g, jsonify, request
from flask_cors import CORS
from sqlalchemy import text
from werkzeug.exceptions import HTTPException

from app.config import Config
from app.extensions import db, jwt, limiter, migrate
from app.routes import API_V1_PREFIX, register_blueprints
from app.services import TokenBlocklistService


def _configure_logging(app: Flask) -> None:
    """
    Structured-ish JSON logs via stdlib logging.

    Chose plain logging + JSON formatter over structlog to avoid an extra
    dependency while still producing machine-parseable request lines.
    """
    level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            '{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":%(message)s}'
        )
    )
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    app.logger.setLevel(level)
    app.logger.propagate = False


def _init_sentry(app: Flask) -> None:
    dsn = os.getenv("SENTRY_DSN", "").strip()
    if not dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration

        sentry_sdk.init(
            dsn=dsn,
            integrations=[FlaskIntegration()],
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.0")),
            environment=os.getenv("SENTRY_ENVIRONMENT", "development"),
        )
        app.logger.info('"Sentry enabled"')
    except Exception as exc:  # pragma: no cover
        app.logger.warning('"Sentry init failed: %s"' % exc)


def create_app(config_overrides=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)

    _configure_logging(app)
    _init_sentry(app)

    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
    if "*" in origins:
        raise RuntimeError(
            "CORS_ORIGINS cannot include '*' when using credentialed cookies. "
            "List explicit frontend origins instead."
        )
    CORS(
        app,
        resources={r"/*": {"origins": origins}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization", "X-CSRF-TOKEN", "X-CSRF-Token"],
        expose_headers=["Content-Type"],
    )

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)

    from app.models import Favorite, Ingredient, Recipe, TokenBlocklist, User  # noqa: F401

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return db.session.get(User, int(identity))

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(_jwt_header, jwt_payload):
        return TokenBlocklistService.is_blocklisted(jwt_payload.get("jti"))

    register_blueprints(app)

    Swagger(
        app,
        template={
            "swagger": "2.0",
            "info": {
                "title": "AI Chef API",
                "description": (
                    "AI-powered food quantity calculator API (v1).\n\n"
                    "All business routes live under `/api/v1`.\n"
                    "Browser clients authenticate with httpOnly JWT cookies "
                    "(access + refresh) and send `X-CSRF-TOKEN` on mutating requests. "
                    "Swagger / API clients may still use `Authorization: Bearer <access_token>`."
                ),
                "version": "1.2.0",
            },
            "securityDefinitions": {
                "Bearer": {
                    "type": "apiKey",
                    "name": "Authorization",
                    "in": "header",
                    "description": "Bearer <access_token>",
                },
                "CookieAuth": {
                    "type": "apiKey",
