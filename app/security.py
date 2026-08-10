from functools import wraps

from flask import g
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app.extensions import db
from app.models import User
from app.utils.responses import error_response


def admin_required(view):
    """Require an active database-backed admin, regardless of frontend state."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        verify_jwt_in_request()
        try:
            user_id = int(get_jwt_identity())
        except (TypeError, ValueError):
            return error_response("Invalid authenticated user.", 401)
        user = db.session.get(User, user_id)
        if not user or not user.is_active:
            return error_response("This account is not active.", 403)
        if user.role != "admin":
            return error_response(
                "You do not have permission to perform this action.", 403
            )
        g.admin_user = user
        return view(*args, **kwargs)

    return wrapped
