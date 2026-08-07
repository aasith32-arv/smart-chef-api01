from app.extensions import db
from app.utils import utc_now


class TokenBlocklist(db.Model):
    """Revoked JWT JTIs (access + refresh)."""

    __tablename__ = "token_blocklist"

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, unique=True, index=True)
    token_type = db.Column(db.String(16), nullable=False)
    user_id = db.Column(db.Integer, nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f"<TokenBlocklist {self.token_type}:{self.jti}>"
