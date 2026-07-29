# payments/services/africanmoney_service.py

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class AfricanMoneyError(Exception):
    pass


class AfricanMoneyService:
    """
    Server-side client for the africanmoney.net collection API.

    - create_collection() POSTs to /collection/create with the api_key and
      returns the hosted payment-page URL plus African Money's collection id.
      The API may answer with either a 302 redirect (Location header) or a
      JSON body containing data.authorization_url; both are handled.
    - verify_collection() GETs /collection/{id}/verify with the SECRET key as
      a Bearer token and returns the payment record. Only credit an order when
      the returned data.status == "completed" and amount/currency match.
    """

    # Keys a payment-page URL might live under in a JSON response.
    URL_KEYS = ("payment_url", "url", "link", "checkout_url", "authorization_url", "redirect_url")

    # africanmoney.net sits behind ModSecurity, which returns 406 to the default
    # python-requests User-Agent. Send browser-like headers so the WAF lets us through.
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        ),
        "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
    }

    @classmethod
    def create_collection(cls, *, item_name, amount, email, phone, client_name,
                          success_url, failed_url):
        """
        Create a collection. Returns a dict:
            {"payment_url": str, "collection_id": str|None, "reference": str|None}
        """
        payload = {
            "item_name": item_name,
            "amount": int(amount),
            "email": email,
            "phone": phone or "0000000000",
            "client_name": client_name or email,
            "success_url": success_url,
            "failed_url": failed_url,
            "api_key": settings.AFRICANMONEY_API_KEY,
        }

        response = requests.post(
            settings.AFRICANMONEY_COLLECTION_URL,
            data=payload,
            headers=cls.HEADERS,
            allow_redirects=False,
            timeout=30,
        )

        logger.info(
            "africanmoney collection/create -> %s %s | body: %.500s",
            response.status_code,
            response.headers.get("Content-Type", ""),
            response.text,
        )

        # Case 1: the API redirects straight to the payment page.
        if response.is_redirect:
            url = response.headers["Location"]
            return {"payment_url": url, "collection_id": cls._id_from_url(url), "reference": None}

        if response.status_code >= 400:
            raise AfricanMoneyError(
                f"africanmoney returned {response.status_code}: {response.text[:300]}"
            )

        # Case 2: JSON response containing a payment URL.
        try:
            data = response.json()
        except ValueError:
            raise AfricanMoneyError(
                "africanmoney returned a non-JSON, non-redirect response: "
                f"{response.text[:300]}"
            )

        url = cls._find_url(data)
        if not url:
            raise AfricanMoneyError(
                f"No payment URL found in africanmoney response: {str(data)[:300]}"
            )

        inner = data.get("data") if isinstance(data.get("data"), dict) else {}
        return {
            "payment_url": url,
            "collection_id": inner.get("id") or cls._id_from_url(url),
            "reference": inner.get("reference"),
        }

    @classmethod
    def verify_collection(cls, collection_id):
        """
        Verify a collection server-side. Returns the `data` dict, e.g.
            {"id":..., "reference":..., "amount":100, "currency":"NGN",
             "status":"completed"|"pending", "email":...}
        Raises AfricanMoneyError if the call fails or the API is unhappy.
        """
        secret = settings.AFRICANMONEY_SECRET_KEY or settings.AFRICANMONEY_API_KEY
        if not secret:
            raise AfricanMoneyError("AFRICANMONEY_SECRET_KEY is not configured")

        url = f"{settings.AFRICANMONEY_BASE_URL}/collection/{collection_id}/verify"
        headers = dict(cls.HEADERS)
        headers["Authorization"] = f"Bearer {secret}"

        response = requests.get(url, headers=headers, allow_redirects=False, timeout=30)

        logger.info(
            "africanmoney verify %s -> %s | body: %.400s",
            collection_id, response.status_code, response.text,
        )

        try:
            payload = response.json()
        except ValueError:
            raise AfricanMoneyError(
                f"verify returned non-JSON {response.status_code}: {response.text[:200]}"
            )

        if response.status_code != 200 or payload.get("status") != "success":
            raise AfricanMoneyError(
                f"verify failed ({response.status_code}): {str(payload)[:200]}"
            )

        return payload.get("data", {}) or {}

    @staticmethod
    def _id_from_url(url):
        """African Money payment URLs look like .../collection/<id>."""
        if not url:
            return None
        return url.rstrip("/").split("/")[-1] or None

    @classmethod
    def _find_url(cls, data):
        if not isinstance(data, dict):
            return None
        for key in cls.URL_KEYS:
            value = data.get(key)
            if isinstance(value, str) and value.startswith("http"):
                return value
        # Common wrapper: {"status": ..., "data": {...}}
        return cls._find_url(data.get("data"))
