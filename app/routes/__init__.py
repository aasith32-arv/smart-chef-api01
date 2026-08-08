from app.routes.ai_routes import ai_bp
from app.routes.auth_routes import auth_bp
from app.routes.calculator_routes import calculator_bp
from app.routes.cooking_routes import cooking_bp
from app.routes.favorite_routes import favorite_bp
from app.routes.recipe_routes import recipe_bp
from app.routes.recommendation_routes import recommendation_bp

API_V1_PREFIX = "/api/v1"


def register_blueprints(app):
    """Mount all business routes under /api/v1. Keep / and /apidocs unversioned.

    Flask's register_blueprint(url_prefix=...) replaces the blueprint's own
    url_prefix, so we combine API_V1_PREFIX with each blueprint prefix (e.g. /ai).
    """
    for blueprint in (
        auth_bp,
        recipe_bp,
        calculator_bp,
        recommendation_bp,
        favorite_bp,
        ai_bp,
        cooking_bp,
    ):
        bp_prefix = blueprint.url_prefix or ""
        app.register_blueprint(
            blueprint, url_prefix=f"{API_V1_PREFIX}{bp_prefix}"
        )
