from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from company.models import Company

User = get_user_model()


class OnboardingRedirectMiddlewareTests(TestCase):
    """Behaviour of jobwebsite.middleware.onboarding.OnboardingRedirectMiddleware."""

    def setUp(self):
        self.dashboard_url = reverse('dashboard')
        self.settings_url = reverse('dashboard_settings')
        self.company_url = reverse('dashboard_post_a_company')
        self.bookmarks_url = reverse('dashboard_bookmarks')

    def _make_user(self, email, role, onboarding_completed):
        return User.objects.create_user(
            email=email,
            password='pass12345',
            first_name='Test',
            last_name='User',
            role=role,
            onboarding_completed=onboarding_completed,
        )

    def _make_company(self, user):
        return Company.objects.create(
            created_by=user,
            company_name='Acme',
            industry='engineering_and_technical',
            description='We build things.',
        )

    # --- Step 1: incomplete profile ---

    def test_incomplete_user_redirected_to_settings(self):
        user = self._make_user('a@x.com', 'freelancer', onboarding_completed=False)
        self.client.force_login(user)
        res = self.client.get(self.dashboard_url)
        self.assertRedirects(res, self.settings_url, fetch_redirect_response=False)

    def test_incomplete_user_can_reach_settings(self):
        user = self._make_user('b@x.com', 'freelancer', onboarding_completed=False)
        self.client.force_login(user)
        res = self.client.get(self.settings_url)
        self.assertEqual(res.status_code, 200)

    # --- Step 2: employer without a company ---

    def test_completed_employer_without_company_redirected(self):
        user = self._make_user('c@x.com', 'employer', onboarding_completed=True)
        self.client.force_login(user)
        res = self.client.get(self.dashboard_url)
        self.assertRedirects(res, self.company_url, fetch_redirect_response=False)

    def test_completed_employer_without_company_can_reach_company_page(self):
        user = self._make_user('d@x.com', 'employer', onboarding_completed=True)
        self.client.force_login(user)
        res = self.client.get(self.company_url)
        self.assertEqual(res.status_code, 200)

    def test_completed_employer_without_company_can_reach_settings(self):
        # So they can switch their role back to freelancer.
        user = self._make_user('e@x.com', 'employer', onboarding_completed=True)
        self.client.force_login(user)
        res = self.client.get(self.settings_url)
        self.assertEqual(res.status_code, 200)

    def test_completed_employer_with_company_reaches_dashboard(self):
        user = self._make_user('f@x.com', 'employer', onboarding_completed=True)
        self._make_company(user)
        self.client.force_login(user)
        res = self.client.get(self.dashboard_url)
        self.assertEqual(res.status_code, 200)

    # --- Freelancers are unaffected once complete ---

    def test_completed_freelancer_reaches_dashboard(self):
        user = self._make_user('g@x.com', 'freelancer', onboarding_completed=True)
        self.client.force_login(user)
        res = self.client.get(self.dashboard_url)
        self.assertEqual(res.status_code, 200)

    # --- Admins are exempt from the middleware ---

    def test_admin_not_redirected_by_onboarding(self):
        # Admin with an incomplete profile must still reach the dashboard;
        # the middleware short-circuits for role == 'admin'. Use a deeper
        # dashboard page so the dashboard view's own admin redirect does not
        # mask the middleware behaviour under test.
        user = self._make_user('admin@x.com', 'admin', onboarding_completed=False)
        self.client.force_login(user)
        res = self.client.get(self.bookmarks_url)
        self.assertEqual(res.status_code, 200)

    # --- Unauthenticated users are not pushed into onboarding ---

    def test_anonymous_user_not_redirected_to_onboarding(self):
        # No force_login: the request is anonymous. The middleware must not
        # send them to settings/company; the view's own @login_required sends
        # them to the login page instead.
        res = self.client.get(self.dashboard_url)
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login/', res['Location'])
        self.assertNotIn('/dashboard/settings/', res['Location'])
        self.assertNotIn('/dashboard/post-a-company/', res['Location'])

    # --- Non-/dashboard/ paths are unaffected ---

    def test_employer_without_company_can_use_non_dashboard_path(self):
        # An /api/ path must not be hijacked by the onboarding redirect even
        # for an employer who has not registered a company.
        user = self._make_user('api@x.com', 'employer', onboarding_completed=True)
        self.client.force_login(user)
        res = self.client.get('/api/bookmarks/')
        self.assertEqual(res.status_code, 200)

    def test_incomplete_user_can_use_non_dashboard_path(self):
        # An incomplete profile must not trigger a redirect outside /dashboard/.
        user = self._make_user('api2@x.com', 'freelancer', onboarding_completed=False)
        self.client.force_login(user)
        res = self.client.get('/api/bookmarks/')
        self.assertEqual(res.status_code, 200)

    # --- Step 1 takes precedence over Step 2 ---

    def test_incomplete_employer_redirected_to_settings_not_company(self):
        # An employer who has not completed onboarding should hit the Step 1
        # settings redirect, not the Step 2 company redirect.
        user = self._make_user('ie@x.com', 'employer', onboarding_completed=False)
        self.client.force_login(user)
        res = self.client.get(self.dashboard_url)
        self.assertRedirects(res, self.settings_url, fetch_redirect_response=False)

    # --- Employer WITH a company can reach a deeper dashboard page ---

    def test_completed_employer_with_company_reaches_deeper_dashboard_page(self):
        user = self._make_user('deep@x.com', 'employer', onboarding_completed=True)
        self._make_company(user)
        self.client.force_login(user)
        res = self.client.get(self.bookmarks_url)
        self.assertEqual(res.status_code, 200)

    def test_completed_employer_without_company_redirected_from_deeper_page(self):
        # The redirect applies to any /dashboard/ page, not only /dashboard/.
        user = self._make_user('deep2@x.com', 'employer', onboarding_completed=True)
        self.client.force_login(user)
        res = self.client.get(self.bookmarks_url)
        self.assertRedirects(res, self.company_url, fetch_redirect_response=False)
