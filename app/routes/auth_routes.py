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
