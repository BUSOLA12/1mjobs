# payments/services/gateway_service.py

import requests
from django.conf import settings


class PaymentGatewayService:

    BASE_URL = "https://api.paystack.co"

    def initialize_payment(self, amount, email, reference):
        url = f"{self.BASE_URL}/transaction/initialize"

        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "email": email,
            "amount": int(amount * 100),  # Paystack uses kobo
            "reference": reference,
            "callback_url": f"{settings.FRONTEND_URL}/payments/",
        }

        response = requests.post(url, json=payload, headers=headers)
        data = response.json()

        if not data.get("status"):
            raise Exception("Payment initialization failed")

        return data["data"]["authorization_url"]