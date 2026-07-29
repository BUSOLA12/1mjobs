from django.shortcuts import redirect
from django.urls import reverse


class OnboardingRedirectMiddleware:
    """Guide authenticated users through onboarding before they can use the
    dashboard.

    1. Any user with an incomplete profile is sent to the settings page.
    2. An employer who has finished their profile but has not registered a
       company is sent to the company page until a company exists.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)

        if (user and user.is_authenticated
                and getattr(user, 'role', None) != 'admin'):

            path = request.path

            # Only gate dashboard pages (keeps the live check off API/static/etc).
            if path.startswith('/dashboard/'):
                settings_path = reverse('dashboard_settings')

                # Evaluate completeness live so newly-required fields take effect
                # immediately, instead of trusting a possibly-stale stored flag.
                profile = getattr(user, 'user_profile', None)
                complete = profile.recompute_onboarding() if profile else False

                # Step 1: required profile fields must be complete.
                if not complete:
                    if path != settings_path:
                        return redirect('dashboard_settings')
                    return self.get_response(request)

                # Step 2: employers must have a registered company.
                if user.role == 'employer':
                    company_path = reverse('dashboard_post_a_company')
                    allowed = (company_path, settings_path)
                    if path not in allowed and not self._has_company(user):
                        return redirect('dashboard_post_a_company')

        return self.get_response(request)

    @staticmethod
    def _has_company(user):
        # Imported lazily so the middleware module stays import-safe at startup.
        from company.models import Company
        return Company.objects.filter(created_by=user).exists()
