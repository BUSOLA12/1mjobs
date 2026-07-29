from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


class UserRoleUpdateViewTests(TestCase):
    """PATCH /api/users/role/ — the company-onboarding back-out endpoint."""

    URL = "/api/users/role/"

    def setUp(self):
        self.client = APIClient()

    def _make_user(self, email, role):
        return User.objects.create_user(
            email=email, password="pass12345", role=role, onboarding_completed=True,
        )

    def test_employer_can_switch_back_to_freelancer(self):
        user = self._make_user("e@x.com", "employer")
        self.client.force_authenticate(user)
        res = self.client.patch(self.URL, {"role": "freelancer"}, format="json")
        self.assertEqual(res.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.role, "freelancer")

    def test_freelancer_can_switch_to_employer(self):
        user = self._make_user("f@x.com", "freelancer")
        self.client.force_authenticate(user)
        res = self.client.patch(self.URL, {"role": "employer"}, format="json")
        self.assertEqual(res.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.role, "employer")

    def test_invalid_role_rejected(self):
        user = self._make_user("g@x.com", "employer")
        self.client.force_authenticate(user)
        res = self.client.patch(self.URL, {"role": "superuser"}, format="json")
        self.assertEqual(res.status_code, 400)
        user.refresh_from_db()
        self.assertEqual(user.role, "employer")

    def test_cannot_self_assign_admin(self):
        user = self._make_user("h@x.com", "employer")
        self.client.force_authenticate(user)
        res = self.client.patch(self.URL, {"role": "admin"}, format="json")
        self.assertEqual(res.status_code, 400)
        user.refresh_from_db()
        self.assertEqual(user.role, "employer")

    def test_admin_cannot_change_role(self):
        user = self._make_user("a@x.com", "admin")
        self.client.force_authenticate(user)
        res = self.client.patch(self.URL, {"role": "freelancer"}, format="json")
        self.assertEqual(res.status_code, 403)
        user.refresh_from_db()
        self.assertEqual(user.role, "admin")

    def test_unauthenticated_rejected(self):
        res = self.client.patch(self.URL, {"role": "freelancer"}, format="json")
        self.assertIn(res.status_code, (401, 403))

    def test_role_switch_does_not_clear_skills(self):
        # Regression: the dedicated endpoint must not touch the profile/skills.
        from users.models import UserProfile, Skill
        user = self._make_user("s@x.com", "employer")
        profile, _ = UserProfile.objects.get_or_create(user=user)
        skill = Skill.objects.create(name="Python")
        profile.skills.add(skill)
        self.client.force_authenticate(user)
        res = self.client.patch(self.URL, {"role": "freelancer"}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(profile.skills.count(), 1)
