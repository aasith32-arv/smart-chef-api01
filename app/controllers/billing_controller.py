import stripe
from flask import request
from flask_jwt_extended import get_jwt_identity

from app.services import BillingConfigurationError, BillingService
from app.utils.responses import error_response, success_response


class BillingController:
    @staticmethod
    def checkout(kind):
        try:
            data = BillingService.create_checkout(int(get_jwt_identity()), kind)
            return success_response(data, "Checkout session created.", 201)
        except (BillingConfigurationError, ValueError) as exc:
            return error_response(str(exc), 400)
        except stripe.StripeError:
            return error_response("Stripe could not create the checkout session.", 502)

    @staticmethod
    def portal():
        try:
            data = BillingService.create_portal(int(get_jwt_identity()))
            return success_response(data, "Billing portal session created.", 201)
        except (BillingConfigurationError, ValueError) as exc:
            return error_response(str(exc), 400)
        except stripe.StripeError:
            return error_response("Stripe could not create the billing portal.", 502)

    @staticmethod
    def status():
        return success_response(BillingService.status(int(get_jwt_identity())), "Billing status retrieved.")

    @staticmethod
    def webhook():
        try:
            processed = BillingService.process_webhook(
                request.get_data(cache=False, as_text=False),
                request.headers.get("Stripe-Signature", ""),
            )
            return success_response({"processed": processed}, "Webhook accepted.")
        except (ValueError, stripe.SignatureVerificationError):
            return error_response("Invalid Stripe webhook signature.", 400)
        except BillingConfigurationError as exc:
            return error_response(str(exc), 503)
