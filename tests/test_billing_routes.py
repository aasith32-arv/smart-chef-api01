from types import SimpleNamespace

from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models import AdvertisingOrder, BillingCustomer, StripeWebhookEvent, Subscription
from app.services.billing_service import ADVERTISING_AMOUNT, SUBSCRIPTION_AMOUNT


def auth_headers(app, user_id):
    with app.app_context():
        token = create_access_token(identity=str(user_id))
    return {"Authorization": f"Bearer {token}"}


def test_billing_routes_require_authentication(client):
    status_response = client.get("/api/v1/billing/status")
    assert status_response.status_code == 401
    assert status_response.headers["Cache-Control"] == "private, no-store"
    assert client.post("/api/v1/billing/checkout/subscription").status_code == 401
    assert client.post("/api/v1/billing/checkout/advertising").status_code == 401
    assert client.post("/api/v1/billing/portal").status_code == 401


def test_subscription_checkout_uses_server_owned_monthly_price(
    app, client, sample_user, monkeypatch
):
    app.config["STRIPE_SECRET_KEY"] = "sk_test_safe"
    captured = {}

    def create_customer(**kwargs):
        return SimpleNamespace(id="cus_test")

    def create_session(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(id="cs_test", url="https://checkout.stripe.test/session")

    monkeypatch.setattr("stripe.Customer.create", create_customer)
    monkeypatch.setattr("stripe.checkout.Session.create", create_session)

    response = client.post(
        "/api/v1/billing/checkout/subscription",
        headers=auth_headers(app, sample_user.id),
    )

    assert response.status_code == 201
    assert response.get_json()["data"]["checkout_url"].startswith("https://checkout")
    assert captured["mode"] == "subscription"
    assert captured["line_items"][0]["price_data"]["unit_amount"] == SUBSCRIPTION_AMOUNT
    assert captured["line_items"][0]["price_data"]["currency"] == "lkr"
    assert captured["line_items"][0]["price_data"]["recurring"] == {"interval": "month"}
    assert BillingCustomer.query.filter_by(user_id=sample_user.id).count() == 1


def test_advertising_checkout_creates_pending_order(app, client, sample_user, monkeypatch):
    app.config["STRIPE_SECRET_KEY"] = "sk_test_safe"
    monkeypatch.setattr("stripe.Customer.create", lambda **_: SimpleNamespace(id="cus_ad"))
    monkeypatch.setattr(
        "stripe.checkout.Session.create",
        lambda **_: SimpleNamespace(id="cs_ad", url="https://checkout.stripe.test/ad"),
    )

    response = client.post(
        "/api/v1/billing/checkout/advertising",
        headers=auth_headers(app, sample_user.id),
    )

    assert response.status_code == 201
    order = AdvertisingOrder.query.one()
    assert order.amount == ADVERTISING_AMOUNT
    assert order.payment_status == "pending"
    assert order.review_status == "awaiting_payment"
    assert order.stripe_checkout_session_id == "cs_ad"


def test_signed_webhook_fulfills_advertising_once(app, client, sample_user, monkeypatch):
    app.config.update(STRIPE_SECRET_KEY="sk_test_safe", STRIPE_WEBHOOK_SECRET="whsec_safe")
    order = AdvertisingOrder(
        user_id=sample_user.id,
        stripe_checkout_session_id="cs_ad",
    )
    db.session.add(order)
    db.session.commit()
    event = {
        "id": "evt_ad_paid",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_ad",
                "client_reference_id": str(sample_user.id),
                "payment_intent": "pi_ad",
                "payment_status": "paid",
                "metadata": {
                    "kind": "advertising",
                    "user_id": str(sample_user.id),
                    "advertising_order_id": str(order.id),
                },
            }
        },
    }
    monkeypatch.setattr("stripe.Webhook.construct_event", lambda *_: event)

    first = client.post(
        "/api/v1/billing/webhook",
        data=b"{}",
        headers={"Stripe-Signature": "test"},
    )
    second = client.post(
        "/api/v1/billing/webhook",
        data=b"{}",
        headers={"Stripe-Signature": "test"},
    )

    assert first.status_code == 200
    assert first.get_json()["data"]["processed"] is True
    assert second.get_json()["data"]["processed"] is False
    db.session.refresh(order)
    assert order.payment_status == "paid"
    assert order.review_status == "under_review"
    assert StripeWebhookEvent.query.count() == 1


def test_subscription_webhook_updates_entitlement(app, client, sample_user, monkeypatch):
    app.config.update(STRIPE_SECRET_KEY="sk_test_safe", STRIPE_WEBHOOK_SECRET="whsec_safe")
    event = {
        "id": "evt_subscription",
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_test",
                "status": "active",
                "current_period_end": 1788739200,
                "cancel_at_period_end": False,
                "metadata": {"user_id": str(sample_user.id)},
                "items": {"data": [{"price": {"id": "price_monthly"}}]},
            }
        },
    }
    monkeypatch.setattr("stripe.Webhook.construct_event", lambda *_: event)

    response = client.post(
        "/api/v1/billing/webhook",
        data=b"{}",
        headers={"Stripe-Signature": "test"},
    )

    assert response.status_code == 200
    subscription = Subscription.query.one()
    assert subscription.user_id == sample_user.id
    assert subscription.status == "active"
    assert subscription.stripe_price_id == "price_monthly"


def test_billing_status_returns_subscription_and_orders(app, client, sample_user):
    db.session.add(
        Subscription(
            user_id=sample_user.id,
            stripe_subscription_id="sub_status",
            status="active",
        )
    )
    db.session.add(AdvertisingOrder(user_id=sample_user.id, payment_status="paid", review_status="under_review"))
    db.session.commit()

    response = client.get(
        "/api/v1/billing/status", headers=auth_headers(app, sample_user.id)
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["subscription"]["status"] == "active"
    assert data["advertising_orders"][0]["review_status"] == "under_review"
