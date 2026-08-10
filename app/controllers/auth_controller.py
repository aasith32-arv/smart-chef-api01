from flask import current_app, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    set_access_cookies,
    set_refresh_cookies,
    unset_jwt_cookies,
)

from app.extensions import db
from app.models import User
from app.services import AuthService, TokenBlocklistService
from app.utils.responses import error_response, success_response
from app.validators import validate_login, validate_profile_update, validate_register


class AuthController:
    @staticmethod
    def _issue_auth_cookies(response, user: User):
        identity = str(user.id)
        claims = {"role": user.role}
        access_token = create_access_token(identity=identity, additional_claims=claims)
        refresh_token = create_refresh_token(identity=identity, additional_claims=claims)
        set_access_cookies(response, access_token)
        set_refresh_cookies(response, refresh_token)
        return response

    @staticmethod
    def register():
        cleaned, errors = validate_register(request.get_json(silent=True))
        if errors:
            return error_response("Validation failed.", 400, errors)

        user, message, status = AuthService.register(cleaned)
        if not user:
            return error_response(message, status)

        response, code = success_response(
            {"user": user.to_dict()},
            "User registered successfully.",
            status,
        )
        AuthController._issue_auth_cookies(response, user)
        return response, code

    @staticmethod
    def login():
        cleaned, errors = validate_login(request.get_json(silent=True))
        if errors:
            return error_response("Validation failed.", 400, errors)

        user = AuthService.get_by_email(cleaned["email"])
        if not user or not user.check_password(cleaned["password"]):
            return error_response("Invalid email or password.", 401)
        if not user.is_active:
            return error_response("This account has been suspended.", 403)

        response, code = success_response(
            {"user": user.to_dict()},
            "Login successful.",
        )
        AuthController._issue_auth_cookies(response, user)
        return response, code

    @staticmethod
    def refresh():
        identity = get_jwt_identity()
        user = db.session.get(User, int(identity))
        if not user or not user.is_active:
            return error_response("This account is not active.", 403)
        access_token = create_access_token(
            identity=identity, additional_claims={"role": user.role}
        )
        response, code = success_response(message="Access token refreshed.")
        set_access_cookies(response, access_token)
        return response, code

    @staticmethod
    def logout():
        TokenBlocklistService.revoke_decoded(get_jwt())

        refresh_name = current_app.config.get(
            "JWT_REFRESH_COOKIE_NAME", "refresh_token_cookie"
        )
        TokenBlocklistService.revoke_raw_token(request.cookies.get(refresh_name))

        response, code = success_response(message="Logged out successfully.")
        unset_jwt_cookies(response)
        return response, code

    @staticmethod
    def get_profile():
        user = db.session.get(User, int(get_jwt_identity()))
        if not user:
            return error_response("User not found.", 404)
        return success_response({"user": user.to_dict()}, "Profile retrieved successfully.")

    @staticmethod
    def update_profile():
        cleaned, errors = validate_profile_update(request.get_json(silent=True))
        if errors:
            return error_response("Validation failed.", 400, errors)

        user = db.session.get(User, int(get_jwt_identity()))
        if not user:
            return error_response("User not found.", 404)

        user, message, status = AuthService.update_profile(user, cleaned)
        if not user:
            return error_response(message, status)
        return success_response({"user": user.to_dict()}, "Profile updated successfully.", status)

    @staticmethod
    def delete_profile():
        user = db.session.get(User, int(get_jwt_identity()))
        if not user:
            return error_response("User not found.", 404)
        if (
            user.role == "admin"
            and user.is_active
            and User.query.filter_by(role="admin", is_active=True).count() <= 1
        ):
            return error_response(
                "The final active admin account cannot be deleted.", 409
            )

        TokenBlocklistService.revoke_decoded(get_jwt())
        refresh_name = current_app.config.get(
            "JWT_REFRESH_COOKIE_NAME", "refresh_token_cookie"
        )
        TokenBlocklistService.revoke_raw_token(request.cookies.get(refresh_name))

        AuthService.delete_profile(user)
        response, code = success_response(message="Profile deleted successfully.")
        unset_jwt_cookies(response)
        return response, code
