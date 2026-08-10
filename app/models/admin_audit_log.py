from app.extensions import db
from app.utils import utc_now


class AdminAuditLog(db.Model):
    """Minimal, non-sensitive audit record for privileged management actions."""

    __tablename__ = "admin_audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    admin_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action = db.Column(db.String(80), nullable=False, index=True)
    target_type = db.Column(db.String(40), nullable=False, index=True)
    target_id = db.Column(db.Integer, nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False, index=True)

    admin = db.relationship("User", back_populates="admin_audit_entries")

    def to_dict(self):
        return {
            "id": self.id,
            "admin_user_id": self.admin_user_id,
            "admin": self.admin.username if self.admin else None,
            "action": self.action,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "created_at": self.created_at.isoformat(),
        }
