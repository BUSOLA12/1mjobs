"""Tests for the onboarding redirect flow.

Covers:
  * jobwebsite.middleware.onboarding.OnboardingRedirectMiddleware gating of
    the HTML dashboard pages.
  * users.models.UserProfile.recompute_onboarding().
  * The /api/companies/create/ DRF endpoint permissions + created_by linkage.

These tests do not modify production code. Where a test exposes a real
production bug, the test asserts the *intended* behaviour so the failure is
visible (see test_admin_not_gated_to_settings docstring).
"""

from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from rest_framework.test import APIClient

from users.models import UserProfile
from company.models import Company

from django.contrib.auth import get_user_model

User = get_user_model()


def make_user(email, role, onboarding_completed, password="pass12345"):
    """Create a user (signal auto-creates a UserProfile) with a known state.

    The middleware evaluates completeness live, so a "completed" user must have
    the required profile fields genuinely populated, not just the flag flipped.
    """
    user = User.objects.create_user(email=email, password=password, role=role)
    profile = user.user_profile  # auto-created by signal

    if onboarding_completed:
        user.first_name = "Test"
        user.last_name = "User"
        user.save()
        profile.address = "12 Main St"
        profile.nationality = "Nigeria"
        profile.avatar = SimpleUploadedFile(
            "real-avatar.png", b"fake-image-bytes", content_type="image/png"
        )
        if role == "freelancer":
            profile.tagline = "Experienced developer"
            profile.bio = "I build things."
            profile.hourly_rate = 50
        profile.save()
        if role == "freelancer":
            from users.models import Skill
            profile.skills.add(Skill.objects.get_or_create(name="Python")[0])
        profile.recompute_onboarding()  # syncs onboarding_completed -> True

    return user


class MiddlewareRedirectTests(TestCase):
    def setUp(self):
        self.settings_url = reverse("dashboard_settings")
        self.company_url = reverse("dashboard_post_a_company")
        self.dashboard_url = reverse("dashboard")

    # 1. Incomplete user -> redirected to settings
    def test_incomplete_user_redirected_to_settings(self):
        user = make_user("incomplete@test.com", "freelancer", False)
        self.client.force_login(user)
        resp = self.client.get(self.dashboard_url, follow=False)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], self.settings_url)

    # 2. Incomplete user CAN load settings (200, not redirected)
    def test_incomplete_user_can_load_settings(self):
        user = make_user("incomplete2@test.com", "freelancer", False)
        self.client.force_login(user)
        resp = self.client.get(self.settings_url, follow=False)
        self.assertEqual(resp.status_code, 200)

    # 3. Completed freelancer loads dashboard with 200
    def test_completed_freelancer_loads_dashboard(self):
        user = make_user("freelancer@test.com", "freelancer", True)
        self.client.force_login(user)
        resp = self.client.get(self.dashboard_url, follow=False)
        self.assertEqual(resp.status_code, 200)

    # 4. Completed employer with NO company -> redirected to post-a-company
    def test_completed_employer_no_company_redirected_to_company(self):
        user = make_user("employer@test.com", "employer", True)
        self.client.force_login(user)
        resp = self.client.get(self.dashboard_url, follow=False)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], self.company_url)

    # 5. That employer CAN load post-a-company and settings (no redirect loop)
    def test_completed_employer_no_company_can_load_company_and_settings(self):
        user = make_user("employer2@test.com", "employer", True)
        self.client.force_login(user)

        resp_company = self.client.get(self.company_url, follow=False)
        self.assertEqual(resp_company.status_code, 200)

        resp_settings = self.client.get(self.settings_url, follow=False)
        self.assertEqual(resp_settings.status_code, 200)

    # 6. Completed employer WITH a company loads dashboard with 200
    def test_completed_employer_with_company_loads_dashboard(self):
        user = make_user("employer3@test.com", "employer", True)
        Company.objects.create(
            created_by=user,
            company_name="Acme Co",
            industry="information_technology",
            description="We build things.",
        )
        self.client.force_login(user)
        resp = self.client.get(self.dashboard_url, follow=False)
        self.assertEqual(resp.status_code, 200)

    # 7. Admin is never gated by THIS middleware to settings.
    def test_admin_not_gated_to_settings(self):
        """An incomplete admin must NOT be bounced to /dashboard/settings/ by
        the onboarding middleware. The dashboard *view* itself redirects admins
        elsewhere (to the admin dashboard), so we assert only that the redirect
        target is not the settings page (which would prove middleware gating).
        """
        user = make_user("admin@test.com", "admin", False)
        self.client.force_login(user)
        resp = self.client.get(self.dashboard_url, follow=False)
        # Middleware must not have sent the admin to settings.
        location = resp.get("Location", "")
        self.assertNotEqual(
            location,
            self.settings_url,
            "Admin was incorrectly gated to settings by the onboarding middleware.",
        )


class RecomputeOnboardingTests(TestCase):
    def _profile_with(self, first, last, address, avatar_name):
        user = User.objects.create_user(
            email=f"{first or 'x'}{last or 'y'}@recompute.com",
            password="pass12345",
            role="freelancer",
        )
        user.first_name = first
        user.last_name = last
        user.save()
        profile = user.user_profile  # auto-created by signal
        profile.address = address
        # Freelancer profile fields now also required for onboarding completion.
        profile.nationality = "Nigeria"
        profile.tagline = "Experienced developer"
        profile.bio = "I build things."
        profile.hourly_rate = 50
        if avatar_name is not None:
            profile.avatar = SimpleUploadedFile(
                avatar_name, b"fake-image-bytes", content_type="image/png"
            )
            # SimpleUploadedFile keeps the name passed in; ensure no 'placeholder'.
        profile.save()
        from .models import Skill
        profile.skills.add(Skill.objects.create(name="Python"))
        return user, profile

    def test_recompute_true_when_all_present(self):
        user, profile = self._profile_with(
            "Jane", "Doe", "12 Main St", "real-avatar.png"
        )
        self.assertNotIn("placeholder", profile.avatar.name)
        result = profile.recompute_onboarding()
        self.assertTrue(result)
        user.refresh_from_db()
        self.assertTrue(user.onboarding_completed)

    def test_recompute_false_missing_address(self):
        user, profile = self._profile_with("Jane", "Doe", "", "real-avatar.png")
        self.assertFalse(profile.recompute_onboarding())
        user.refresh_from_db()
        self.assertFalse(user.onboarding_completed)

    def test_recompute_false_missing_last_name(self):
        user, profile = self._profile_with("Jane", "", "12 Main St", "real-avatar.png")
        self.assertFalse(profile.recompute_onboarding())
        user.refresh_from_db()
        self.assertFalse(user.onboarding_completed)

    def test_recompute_false_placeholder_avatar(self):
        # Default avatar is the placeholder; leave it untouched.
        user = User.objects.create_user(
            email="placeholder@recompute.com", password="pass12345", role="freelancer"
        )
        user.first_name = "Jane"
        user.last_name = "Doe"
        user.save()
        profile = user.user_profile
        profile.address = "12 Main St"
        profile.save()
        self.assertIn("placeholder", profile.avatar.name)
        self.assertFalse(profile.recompute_onboarding())
        user.refresh_from_db()
        self.assertFalse(user.onboarding_completed)


class CompanyCreateAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/companies/create/"
        self.valid_payload = {
            "company_name": "Acme Co",
            "industry": "information_technology",
            "description": "We build things.",
        }

    def test_unauthenticated_create_rejected(self):
        resp = self.client.post(self.url, self.valid_payload)
        self.assertIn(resp.status_code, (401, 403))

    def test_authenticated_employer_create_succeeds_and_links_user(self):
        user = make_user("apiemployer@test.com", "employer", True)
        self.client.force_authenticate(user=user)
        resp = self.client.post(self.url, self.valid_payload)
        self.assertEqual(resp.status_code, 201, resp.content)
        company = Company.objects.get(company_name="Acme Co")
        self.assertEqual(company.created_by, user)
