from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.controllers import BillingController

billing_bp = Blueprint("billing", __name__, url_prefix="/billing")

# All routes below (except the Stripe webhook) require a valid JWT access
# token. flask-jwt-extended is configured with JWT_TOKEN_LOCATION =
# ["headers", "cookies"], so jwt_required() accepts either:
#   - an "Authorization: Bearer <access_token>" header (Swagger / API clients), or
#   - the httpOnly "access_token_cookie" set by /api/v1/login (browser clients).
# If neither is present/valid, app.jwt.unauthorized_loader in app/__init__.py
# returns the "Authorization token is required." 401 response and logs the
# request details (path, method, whether a header/cookie was present) to help
# diagnose auth failures.


@billing_bp.post("/checkout/subscription")
@jwt_required()
def subscription_checkout():
    """
    Create a Stripe checkout session for a subscription.
    ---
    tags:
      - Billing
    security:
      - Bearer: []
      - CookieAuth: []
    responses:
      201:
        description: Checkout session created
      401:
        description: Authorization token is required or invalid
    """
    return BillingController.checkout("subscription")


@billing_bp.post("/checkout/advertising")
@jwt_required()
def advertising_checkout():
    """
    Create a Stripe checkout session for advertising.
    ---
    tags:
      - Billing
    security:
      - Bearer: []
      - CookieAuth: []
    responses:
      201:
        description: Checkout session created
      401:
        description: Authorization token is required or invalid
    """
    return BillingController.checkout("advertising")


@billing_bp.post("/portal")
@jwt_required()
def customer_portal():
    """
    Create a Stripe billing portal session.
    ---
    tags:
      - Billing
    security:
      - Bearer: []
      - CookieAuth: []
    responses:
      201:
        description: Billing portal session created
      401:
        description: Authorization token is required or invalid
    """
    return BillingController.portal()


@billing_bp.get("/status")
@jwt_required()
def billing_status():
    """
    Get the authenticated user's billing status.
    ---
    tags:
      - Billing
    security:
      - Bearer: []
      - CookieAuth: []
    responses:
      200:
        description: Billing status retrieved
      401:
        description: Authorization token is required or invalid
    """
    return BillingController.status()


@billing_bp.post("/webhook")
def stripe_webhook():
    return BillingController.webhook()
