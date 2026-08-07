from datetime import datetime, timezone

from flask_jwt_extended import decode_token

from app.extensions import db
from app.models.token_blocklist import TokenBlocklist
from app.utils import utc_now


class TokenBlocklistService:
    @staticmethod
    def is_blocklisted(jti: str) -> bool:
        if not jti:
            return False
        return (
            db.session.query(TokenBlocklist.id)
            .filter_by(jti=jti)
            .first()
            is not None
        )

    @staticmethod
    def revoke_decoded(decoded: dict, user_id: int | None = None) -> None:
        jti = decoded.get("jti")
        if not jti or TokenBlocklistService.is_blocklisted(jti):
            return

        exp = decoded.get("exp")
        if exp is None:
            expires_at = utc_now()
        else:
            expires_at = datetime.fromtimestamp(exp, tz=timezone.utc).replace(tzinfo=None)

        identity = decoded.get("sub")
        resolved_user = user_id
