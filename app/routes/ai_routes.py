from flask import Blueprint

from app.controllers.ai_controller import AIController
from app.extensions import limiter

ai_bp = Blueprint("ai", __name__, url_prefix="/ai")


@ai_bp.route("/status", methods=["GET"])
def ai_status():
    """Return whether an AI provider is configured and the API is reachable."""
    return AIController.status()


@ai_bp.route("/plan", methods=["POST"])
@limiter.limit("20 per minute")
def ai_plan():
    """Generate a scaled meal plan (AI provider when configured, else local recipes)."""
    return AIController.plan()


@ai_bp.route("/suggest", methods=["POST"])
@limiter.limit("30 per minute")
def ai_suggest():
    """Suggest dishes from pantry ingredients."""
    return AIController.suggest()


@ai_bp.route("/translate", methods=["POST"])
@limiter.limit("40 per minute")
def ai_translate():
    """Translate recipe content into the requested language."""
    return AIController.translate()
