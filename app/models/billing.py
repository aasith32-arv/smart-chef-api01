from app.extensions import db
from app.utils import utc_now


class BillingCustomer(db.Model):
    __tablename__ = "billing_customers"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    stripe_customer_id = db.Column(db.String(255), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = db.relationship("User", back_populates="billing_customer")


class Subscription(db.Model):
    __tablename__ = "subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stripe_subscription_id = db.Column(db.String(255), nullable=False, unique=True, index=True)
    stripe_price_id = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(40), nullable=False, default="incomplete", index=True)
    current_period_end = db.Column(db.DateTime, nullable=True)
    cancel_at_period_end = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = db.relationship("User", back_populates="subscriptions")

    def to_dict(self):
        return {
            "status": self.status,
            "current_period_end": self.current_period_end.isoformat() if self.current_period_end else None,
            "cancel_at_period_end": self.cancel_at_period_end,
        }


class AdvertisingOrder(db.Model):
    __tablename__ = "advertising_orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stripe_checkout_session_id = db.Column(db.String(255), nullable=True, unique=True, index=True)
    stripe_payment_intent_id = db.Column(db.String(255), nullable=True, unique=True)
    amount = db.Column(db.Integer, nullable=False, default=200000)
    currency = db.Column(db.String(3), nullable=False, default="lkr")
    payment_status = db.Column(db.String(40), nullable=False, default="pending", index=True)
    review_status = db.Column(db.String(40), nullable=False, default="awaiting_payment", index=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = db.relationship("User", back_populates="advertising_orders")

    def to_dict(self):
        return {
            "id": self.id,
            "amount": self.amount,
            "currency": self.currency,
            "payment_status": self.payment_status,
            "review_status": self.review_status,
            "created_at": self.created_at.isoformat(),
        }


class StripeWebhookEvent(db.Model):
    __tablename__ = "stripe_webhook_events"

    id = db.Column(db.Integer, primary_key=True)
    stripe_event_id = db.Column(db.String(255), nullable=False, unique=True, index=True)
    event_type = db.Column(db.String(120), nullable=False)
    processed_at = db.Column(db.DateTime, default=utc_now, nullable=False)
