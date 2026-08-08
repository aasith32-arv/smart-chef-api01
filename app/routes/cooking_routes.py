from flask import Blueprint

from app.controllers.cooking_controller import CookingController
from app.extensions import limiter

cooking_bp = Blueprint("cooking", __name__, url_prefix="/cooking")


@cooking_bp.route("/troubleshoot", methods=["POST"])
@limiter.limit("30 per minute")
def troubleshoot():
    """Troubleshoot a cooking problem.
    ---
    tags: [Cooking Intelligence]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [problem]
          properties:
            problem: {type: string, example: too watery}
            context: {type: string}
            use_ai: {type: boolean, default: false}
    responses:
      200: {description: Conservative recovery guidance}
      400: {description: Invalid request}
    """
    return CookingController.troubleshoot()


@cooking_bp.route("/substitute", methods=["POST"])
@limiter.limit("30 per minute")
def substitute():
    """Recommend a context-aware ingredient substitution.
    ---
    tags: [Cooking Intelligence]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [ingredient]
          properties:
            ingredient: {type: string, example: yogurt}
            recipe_id: {type: integer}
            recipe_context: {type: string}
            use_ai: {type: boolean, default: false}
    responses:
      200: {description: Substitution options and trade-offs}
      400: {description: Invalid request}
      404: {description: Recipe not found}
    """
    return CookingController.substitute()


@cooking_bp.route("/explain", methods=["POST"])
@limiter.limit("40 per minute")
def explain():
    """Explain why a cooking action belongs at a stage.
    ---
    tags: [Cooking Intelligence]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [action]
          properties:
            action: {type: string, example: add onion now}
            context: {type: string}
            use_ai: {type: boolean, default: false}
    responses:
      200: {description: Beginner-friendly cooking explanation}
      400: {description: Invalid request}
    """
    return CookingController.explain()
