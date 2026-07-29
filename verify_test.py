"""
Standalone script: create an African Money collection, then call the verify
endpoint and print the EXACT raw response the API returns.

Run from the project dir (the one with manage.py) with the venv active:
    python verify_test.py
Keys are read from your .env via Django settings (AFRICANMONEY_API_KEY / _SECRET_KEY).
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jobwebsite.settings")
django.setup()

import requests
from django.conf import settings

BASE = settings.AFRICANMONEY_BASE_URL
API_KEY = settings.AFRICANMONEY_API_KEY
SECRET_KEY = settings.AFRICANMONEY_SECRET_KEY

# Browser-like UA so ModSecurity (WAF) doesn't return 406.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
}


def create_collection():
    """Create a collection and return (id, reference, payment_url)."""
    payload = {
        "item_name": "verify-test",
        "amount": 6000,
        "email": "iyiolaolubusola@gmail.com",
        "phone": "08000000000",
        "client_name": "Verify Test",
        "success_url": "https://one-million-jobs.fly.dev/order-confirmation/",
        "failed_url": "https://one-million-jobs.fly.dev/checkout/1/",
        "api_key": API_KEY,
    }
    r = requests.post(f"{BASE}/collection/create", data=payload,
                      headers=HEADERS, allow_redirects=False, timeout=30)
    data = r.json().get("data", {})
    return data.get("id"), data.get("reference"), data.get("authorization_url")


def call(method, url):
    """Make the request and print the exact raw response."""
    headers = dict(HEADERS)
    headers["Authorization"] = f"Bearer {SECRET_KEY}"

    print("\n" + "=" * 72)
    print(f"REQUEST : {method} {url}")
    print(f"HEADER  : Authorization: Bearer {SECRET_KEY[:10]}...{SECRET_KEY[-4:]}")

    r = requests.request(method, url, headers=headers, allow_redirects=False, timeout=30)

    print("-" * 72)
    print(f"STATUS  : {r.status_code} {r.reason}")
    print(f"CT      : {r.headers.get('Content-Type')}")
    print("RAW RESPONSE BODY (exact):")
    print(r.text)


def main():
    print(f"BASE        : {BASE}")
    print(f"API_KEY     : {API_KEY[:8]}...")
    print(f"SECRET_KEY  : {'(set)' if SECRET_KEY else '(EMPTY)'}")

    cid, ref, pay_url = create_collection()
    print(f"\nCreated collection:")
    print(f"  id          = {cid}")
    print(f"  reference   = {ref}")
    print(f"  payment_url = {pay_url}")

    # The exact endpoint from the docs:
    call("GET", f"{BASE}/collection/{cid}/verify")


if __name__ == "__main__":
    main()
