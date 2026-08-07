from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.controllers import AuthController
from app.extensions import limiter

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
@limiter.limit("5 per minute")
def register():
    """
    Register a new user.
    Sets httpOnly access + refresh JWT cookies (tokens are not returned in JSON).
    ---
    tags:
      - Auth
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [username, email, password]
          properties:
            username: {type: string}
            email: {type: string}
            password: {type: string}
            full_name: {type: string}
    responses:
      201:
        description: Registered; Set-Cookie headers include access/refresh JWTs
    """
    return AuthController.register()


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    """
    Login and set httpOnly JWT cookies.
    ---
    tags:
      - Auth
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [email, password]
          properties:
            email: {type: string}
            password: {type: string}
    responses:
      200:
        description: Logged in; cookies set
    """
    return AuthController.login()


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
@limiter.limit("30 per minute")
def refresh():
    """
    Issue a new access-token cookie using the refresh-token cookie.
    Requires csrf_refresh_token as X-CSRF-TOKEN when using cookies.
    ---
    tags:
      - Auth
    responses:
      200:
        description: Access cookie refreshed
    """
    return AuthController.refresh()


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """
    Revoke current tokens and clear JWT cookies.
    ---
    tags:
      - Auth
    responses:
      200:
        description: Logged out
    """
    return AuthController.logout()


@auth_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    """Get the authenticated user's profile (session check /auth me)."""
    return AuthController.get_profile()


@auth_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    """Update the authenticated user's profile."""
    return AuthController.update_profile()


@auth_bp.route("/profile", methods=["DELETE"])
@jwt_required()
def delete_profile():
    """Delete the authenticated user's profile and clear cookies."""
    return AuthController.delete_profile()
