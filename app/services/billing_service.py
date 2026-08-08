from datetime import datetime, timezone

import stripe
from flask import current_app

from app.extensions import db
from app.models import (
    AdvertisingOrder,
    BillingCustomer,
    StripeWebhookEvent,
    Subscription,
    User,
)

SUBSCRIPTION_AMOUNT = 120000
ADVERTISING_AMOUNT = 200000
CURRENCY = "lkr"


class BillingConfigurationError(RuntimeError):
    pass


def _value(obj, key, default=None):
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _timestamp(value):
    if not value:
        return None
    return datetime.fromtimestamp(int(value), tz=timezone.utc).replace(tzinfo=None)


class BillingService:
    @staticmethod
    def _configure():
        secret = current_app.config.get("STRIPE_SECRET_KEY", "")
        if not secret:
            raise BillingConfigurationError("Stripe payments are not configured.")
        stripe.api_key = secret

    @staticmethod
    def _customer_for(user: User):
        existing = BillingCustomer.query.filter_by(user_id=user.id).first()
        if existing:
            return existing

        customer = stripe.Customer.create(
            email=user.email,
            name=user.full_name or user.username,
            metadata={"ai_chef_user_id": str(user.id)},
        )
        record = BillingCustomer(user_id=user.id, stripe_customer_id=customer.id)
        db.session.add(record)
        db.session.commit()
        return record

    @staticmethod
    def _line_item(kind: str):
        if kind == "subscription":
            price_id = current_app.config.get("STRIPE_SUBSCRIPTION_PRICE_ID")
            if price_id:
                return {"price": price_id, "quantity": 1}
            return {
                "price_data": {
                    "currency": CURRENCY,
                    "unit_amount": SUBSCRIPTION_AMOUNT,
                    "recurring": {"interval": "month"},
                    "product_data": {"name": "AI Chef Premium"},
                },
                "quantity": 1,
            }

        price_id = current_app.config.get("STRIPE_ADVERTISING_PRICE_ID")
        if price_id:
            return {"price": price_id, "quantity": 1}
        return {
            "price_data": {
                "currency": CURRENCY,
                "unit_amount": ADVERTISING_AMOUNT,
                "product_data": {"name": "AI Chef Advertising Package"},
            },
            "quantity": 1,
        }

    @classmethod
    def create_checkout(cls, user_id: int, kind: str):
        cls._configure()
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError("User not found.")
        if kind not in {"subscription", "advertising"}:
            raise ValueError("Unsupported billing product.")

        if kind == "subscription":
            active = Subscription.query.filter(
                Subscription.user_id == user_id,
                Subscription.status.in_(("active", "trialing")),
            ).first()
            if active:
                raise ValueError("You already have an active subscription.")

        customer = cls._customer_for(user)
        frontend = current_app.config["FRONTEND_URL"]
        metadata = {"kind": kind, "user_id": str(user.id)}
        order = None
        if kind == "advertising":
            order = AdvertisingOrder(user_id=user.id)
            db.session.add(order)
            db.session.commit()
            metadata["advertising_order_id"] = str(order.id)

        params = {
            "customer": customer.stripe_customer_id,
            "client_reference_id": str(user.id),
            "mode": "subscription" if kind == "subscription" else "payment",
            "line_items": [cls._line_item(kind)],
            "metadata": metadata,
            "success_url": f"{frontend}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": f"{frontend}/pricing?checkout=cancelled",
        }
        if kind == "subscription":
            params["subscription_data"] = {"metadata": {"user_id": str(user.id)}}

        try:
            session = stripe.checkout.Session.create(**params)
        except Exception:
            if order:
                db.session.delete(order)
                db.session.commit()
            raise

        if order:
            order.stripe_checkout_session_id = session.id
            db.session.commit()
        return {"checkout_url": session.url, "session_id": session.id}

    @classmethod
    def create_portal(cls, user_id: int):
        cls._configure()
        customer = BillingCustomer.query.filter_by(user_id=user_id).first()
        if not customer:
            raise ValueError("No billing account exists for this user.")
        session = stripe.billing_portal.Session.create(
            customer=customer.stripe_customer_id,
            return_url=f"{current_app.config['FRONTEND_URL']}/profile",
        )
        return {"portal_url": session.url}

    @staticmethod
    def status(user_id: int):
        subscription = (
            Subscription.query.filter_by(user_id=user_id)
            .order_by(Subscription.updated_at.desc())
            .first()
        )
        orders = (
            AdvertisingOrder.query.filter_by(user_id=user_id)
            .order_by(AdvertisingOrder.created_at.desc())
            .all()
        )
        return {
            "subscription": subscription.to_dict() if subscription else None,
            "advertising_orders": [order.to_dict() for order in orders],
        }

    @classmethod
    def process_webhook(cls, payload: bytes, signature: str):
        cls._configure()
        secret = current_app.config.get("STRIPE_WEBHOOK_SECRET", "")
        if not secret:
            raise BillingConfigurationError("Stripe webhook verification is not configured.")
        event = stripe.Webhook.construct_event(payload, signature, secret)
        event_id = _value(event, "id")
        event_type = _value(event, "type")
        if StripeWebhookEvent.query.filter_by(stripe_event_id=event_id).first():
            return False

        obj = _value(_value(event, "data", {}), "object", {})
        if event_type in {"checkout.session.completed", "checkout.session.async_payment_succeeded"}:
            cls._handle_checkout(obj)
        elif event_type in {"customer.subscription.created", "customer.subscription.updated", "customer.subscription.deleted"}:
            cls._upsert_subscription(obj)
        elif event_type in {"invoice.paid", "invoice.payment_failed"}:
            subscription_id = _value(obj, "subscription")
            if subscription_id:
                remote = stripe.Subscription.retrieve(subscription_id)
                cls._upsert_subscription(remote)

        db.session.add(StripeWebhookEvent(stripe_event_id=event_id, event_type=event_type))
        db.session.commit()
        return True

    @classmethod
    def _handle_checkout(cls, session):
        metadata = _value(session, "metadata", {}) or {}
        kind = _value(metadata, "kind")
        user_id = int(_value(metadata, "user_id") or _value(session, "client_reference_id"))
        if kind == "subscription" and _value(session, "subscription"):
            remote = stripe.Subscription.retrieve(_value(session, "subscription"))
            cls._upsert_subscription(remote, user_id=user_id)
        elif kind == "advertising":
            order_id = int(_value(metadata, "advertising_order_id"))
            order = db.session.get(AdvertisingOrder, order_id)
            if (
                order
                and order.user_id == user_id
                and _value(session, "payment_status") == "paid"
            ):
                order.stripe_payment_intent_id = _value(session, "payment_intent")
                order.payment_status = "paid"
                order.review_status = "under_review"

    @staticmethod
    def _upsert_subscription(remote, user_id=None):
        subscription_id = _value(remote, "id")
        metadata = _value(remote, "metadata", {}) or {}
        resolved_user_id = user_id or int(_value(metadata, "user_id"))
        record = Subscription.query.filter_by(stripe_subscription_id=subscription_id).first()
        if not record:
            record = Subscription(user_id=resolved_user_id, stripe_subscription_id=subscription_id)
            db.session.add(record)

        items = _value(_value(remote, "items", {}), "data", []) or []
        first_price = _value(items[0], "price") if items else None
        record.stripe_price_id = _value(first_price, "id")
        record.status = _value(remote, "status", "incomplete")
        record.current_period_end = _timestamp(_value(remote, "current_period_end"))
        record.cancel_at_period_end = bool(_value(remote, "cancel_at_period_end", False))
