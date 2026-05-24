import razorpay
from django.conf import settings


def get_razorpay_client():
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        raise ValueError("Razorpay keys are missing. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET.")

    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def create_razorpay_order(plan, receipt):
    client = get_razorpay_client()
    return client.order.create(
        {
            "amount": plan.amount_in_paise,
            "currency": "INR",
            "receipt": receipt,
            "payment_capture": 1,
        }
    )


def verify_razorpay_signature(payment_data):
    client = get_razorpay_client()
    client.utility.verify_payment_signature(payment_data)
