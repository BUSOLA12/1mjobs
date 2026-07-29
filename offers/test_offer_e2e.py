"""End-to-end checks for the offers feature (API layer).

Run with: python manage.py test offers.test_offer_e2e -v 2
Uses Django's test database, so the real db.sqlite3 is never touched.
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APITestCase

from pricing.models import Plan, PlanFeature, Subscription
from .models import Offer, OfferFile

User = get_user_model()


def make_subscription(user, offers_limit=5):
    plan = Plan.objects.create(
        name="Test Plan", user_type="employer", monthly_price=1000
    )
    PlanFeature.objects.create(plan=plan, feature_name="offers", limit=offers_limit)
    return Subscription.objects.create(
        user=user,
        plan=plan,
        billing_cycle="monthly",
        end_date=timezone.now() + timedelta(days=30),
    )


class OfferE2ETest(APITestCase):
    def setUp(self):
        self.sender = User.objects.create_user(
            email="sender@test.com", password="pass12345",
            first_name="Sade", last_name="Employer", role="employer",
        )
        self.receiver = User.objects.create_user(
            email="receiver@test.com", password="pass12345",
            first_name="Femi", last_name="Freelancer", role="freelancer",
        )
        self.stranger = User.objects.create_user(
            email="stranger@test.com", password="pass12345",
            first_name="Tunde", last_name="Stranger", role="freelancer",
        )

    # ---- Create ----

    def test_create_requires_auth(self):
        resp = self.client.post("/api/offers/create/", {"receiver": self.receiver.id})
        self.assertIn(resp.status_code, (401, 403))

    def test_create_without_subscription_is_denied(self):
        self.client.force_authenticate(self.sender)
        resp = self.client.post(
            "/api/offers/create/",
            {"receiver": self.receiver.id, "message": "Hello"},
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(Offer.objects.count(), 0)

    def test_create_with_subscription_succeeds_and_consumes_feature(self):
        sub = make_subscription(self.sender, offers_limit=2)
        self.client.force_authenticate(self.sender)
        resp = self.client.post(
            "/api/offers/create/",
            {"receiver": self.receiver.id, "message": "Work with us"},
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        offer = Offer.objects.get()
        self.assertEqual(offer.sender, self.sender)
        self.assertEqual(offer.receiver, self.receiver)
        self.assertEqual(offer.sender_email, "sender@test.com")
        self.assertEqual(offer.sender_full_name, "Sade Employer")
        sub.refresh_from_db()
        self.assertEqual(sub.remaining_features["offers"], 1)

    def test_create_with_file_attachments(self):
        make_subscription(self.sender)
        self.client.force_authenticate(self.sender)
        f1 = SimpleUploadedFile("brief.txt", b"project brief", content_type="text/plain")
        f2 = SimpleUploadedFile("specs.txt", b"specs", content_type="text/plain")
        resp = self.client.post(
            "/api/offers/create/",
            {"receiver": self.receiver.id, "message": "With files",
             "uploaded_files": [f1, f2]},
            format="multipart",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(OfferFile.objects.filter(offer__sender=self.sender).count(), 2)

    def test_freelancer_cannot_send_even_with_subscription(self):
        make_subscription(self.stranger)  # freelancer with an offers feature
        self.client.force_authenticate(self.stranger)
        resp = self.client.post(
            "/api/offers/create/",
            {"receiver": self.receiver.id, "message": "freelancer trying"},
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(Offer.objects.count(), 0)

    def test_cannot_send_offer_to_employer(self):
        other_employer = User.objects.create_user(
            email="boss@test.com", password="pass12345",
            first_name="Bola", last_name="Boss", role="employer",
        )
        sub = make_subscription(self.sender, offers_limit=2)
        self.client.force_authenticate(self.sender)
        resp = self.client.post(
            "/api/offers/create/",
            {"receiver": other_employer.id, "message": "to employer"},
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(Offer.objects.count(), 0)
        # Denied before the feature is consumed
        sub.refresh_from_db()
        self.assertEqual(sub.remaining_features["offers"], 2)

    def test_create_denied_when_limit_exhausted(self):
        make_subscription(self.sender, offers_limit=1)
        self.client.force_authenticate(self.sender)
        first = self.client.post(
            "/api/offers/create/", {"receiver": self.receiver.id, "message": "one"}
        )
        self.assertEqual(first.status_code, 201)
        second = self.client.post(
            "/api/offers/create/", {"receiver": self.receiver.id, "message": "two"}
        )
        self.assertEqual(second.status_code, 403)
        self.assertEqual(Offer.objects.count(), 1)

    # ---- Lists ----

    def _make_offer(self, days_old=0, message="hi"):
        offer = Offer.objects.create(
            sender=self.sender, receiver=self.receiver,
            sender_full_name="Sade Employer", sender_email=self.sender.email,
            message=message,
        )
        if days_old:
            Offer.objects.filter(pk=offer.pk).update(
                created_at=timezone.now() - timedelta(days=days_old)
            )
        return offer

    def test_received_list_with_subscription_shows_all(self):
        make_subscription(self.receiver)
        self._make_offer(days_old=0)
        self._make_offer(days_old=50)
        self.client.force_authenticate(self.receiver)
        resp = self.client.get("/api/offers/received/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["offers"]), 2)
        self.assertIsNone(resp.data["unlisted"])

    def test_received_list_without_subscription_hides_recent(self):
        self._make_offer(days_old=0)   # recent -> hidden
        self._make_offer(days_old=50)  # old -> visible
        self.client.force_authenticate(self.receiver)
        resp = self.client.get("/api/offers/received/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["offers"]), 1)
        self.assertEqual(resp.data["unlisted"], 1)

    def test_sent_list(self):
        self._make_offer()
        self.client.force_authenticate(self.sender)
        resp = self.client.get("/api/offers/sent/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["receiver"]["email"], "receiver@test.com")

    # ---- Detail ----

    def test_detail_visible_to_sender_and_receiver_only(self):
        offer = self._make_offer(message="secret")
        for user in (self.sender, self.receiver):
            self.client.force_authenticate(user)
            resp = self.client.get(f"/api/offers/{offer.id}/")
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.data["message"], "secret")
        self.client.force_authenticate(self.stranger)
        resp = self.client.get(f"/api/offers/{offer.id}/")
        self.assertEqual(resp.status_code, 403)

    # ---- Delete ----

    def test_delete_only_by_sender(self):
        offer = self._make_offer()
        self.client.force_authenticate(self.receiver)
        resp = self.client.delete(f"/api/offers/{offer.id}/delete/")
        self.assertEqual(resp.status_code, 403)
        self.assertTrue(Offer.objects.filter(pk=offer.pk).exists())

        self.client.force_authenticate(self.sender)
        resp = self.client.delete(f"/api/offers/{offer.id}/delete/")
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(Offer.objects.filter(pk=offer.pk).exists())
