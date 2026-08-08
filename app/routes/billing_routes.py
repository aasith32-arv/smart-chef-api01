from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.controllers import BillingController

billing_bp = Blueprint("billing", __name__, url_prefix="/billing")


@billing_bp.post("/checkout/subscription")
@jwt_required()
def subscription_checkout():
    return BillingController.checkout("subscription")


@billing_bp.post("/checkout/advertising")
@jwt_required()
def advertising_checkout():
    return BillingController.checkout("advertising")


@billing_bp.post("/portal")
@jwt_required()
def customer_portal():
    return BillingController.portal()


@billing_bp.get("/status")
@jwt_required()
def billing_status():
    return BillingController.status()


@billing_bp.post("/webhook")
def stripe_webhook():
    return BillingController.webhook()
