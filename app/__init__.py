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
                    "name": "Cookie",
                    "in": "header",
                    "description": "access_token_cookie + X-CSRF-TOKEN for mutations",
                },
            },
        },
    )

    @app.before_request
    def _start_timer():
        g._request_start = time.perf_counter()

    @app.after_request
    def _log_request(response):
        started = getattr(g, "_request_start", None)
        latency_ms = None
        if started is not None:
            latency_ms = round((time.perf_counter() - started) * 1000, 2)
        app.logger.info(
            '{"method":"%s","path":"%s","status":%s,"latency_ms":%s}'
            % (request.method, request.path, response.status_code, latency_ms)
        )
        return response

    @app.route("/", methods=["GET"])
    def api_home():
        return jsonify(
            {
                "message": "AI Chef – Smart Food Quantity Calculator API",
                "version": "1.2.0",
                "documentation": "/apidocs",
                "health": "/health",
                "api_base": API_V1_PREFIX,
                "auth": {
                    "mode": "httpOnly cookies (access + refresh) with CSRF; Bearer header still accepted",
                    "access_ttl_minutes": int(
                        app.config["JWT_ACCESS_TOKEN_EXPIRES"].total_seconds() // 60
                    ),
                    "refresh_ttl_days": int(
                        app.config["JWT_REFRESH_TOKEN_EXPIRES"].total_seconds() // 86400
                    ),
                },
                "endpoints": {
                    "auth": {
                        "register": f"POST {API_V1_PREFIX}/register",
                        "login": f"POST {API_V1_PREFIX}/login",
                        "refresh": f"POST {API_V1_PREFIX}/refresh",
                        "logout": f"POST {API_V1_PREFIX}/logout",
                        "profile": f"GET {API_V1_PREFIX}/profile",
                    },
                    "recipes": f"GET {API_V1_PREFIX}/recipes",
                    "calculator": f"POST {API_V1_PREFIX}/calculate",
                    "recommendation": f"POST {API_V1_PREFIX}/recommend",
                    "ai": f"{API_V1_PREFIX}/ai/*",
                    "favorites": f"{API_V1_PREFIX}/favorites",
                },
            }
        )

    @app.route("/health", methods=["GET"])
    def health():
        """Liveness/readiness: verifies DB connectivity with SELECT 1."""
        try:
            db.session.execute(text("SELECT 1"))
            return jsonify({"status": "ok", "database": "up"}), 200
        except Exception as exc:
            app.logger.exception('"health check failed"')
            return (
                jsonify(
                    {
                        "status": "degraded",
                        "database": "down",
                        "detail": str(exc.__class__.__name__),
                    }
                ),
                503,
            )

    @app.cli.command("seed")
    def seed_command():
        """Seed sample recipes (flask seed)."""
        from app.seeders import seed_recipes

        seed_recipes()
        print("Database seeded successfully.")

    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        return jsonify({"success": False, "message": err.description}), err.code

    @app.errorhandler(404)
    def handle_not_found(err):
        return jsonify({"success": False, "message": "Resource not found."}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(err):
        return jsonify({"success": False, "message": "Method not allowed."}), 405

    @app.errorhandler(429)
    def handle_rate_limit(err):
        return jsonify({"success": False, "message": "Too many requests. Please try again later."}), 429

    @app.errorhandler(500)
    def handle_internal_error(err):
        db.session.rollback()
        app.logger.exception('"unhandled server error"')
        return jsonify({"success": False, "message": "An internal server error occurred."}), 500

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"success": False, "message": "Token has expired."}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"success": False, "message": "Invalid token."}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"success": False, "message": "Authorization token is required."}), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({"success": False, "message": "Token has been revoked."}), 401

    return app
