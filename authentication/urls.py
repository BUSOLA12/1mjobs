from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('login/', views.LoginView.as_view()),
    path('logout/', views.LogoutView.as_view()),
    path('register/', views.RegisterView.as_view()),

    path("verify-email-otp/", views.VerifyEmailOTPView.as_view(), name="verify-email-otp"),

    path('update-password/', views.UpdatePasswordView.as_view()),
    path('reset-password/', views.ResetPasswordRequestView.as_view()),
    path('reset-password/confirm/', views.ResetPasswordConfirmView.as_view()),
    path('two-factor/request/', views.TwoFactorRequestView.as_view()),
    path('two-factor/verify/', views.TwoFactorVerifyView.as_view()),

    # Social Auth
    path("google/", views.GoogleAuthInitView.as_view(), name="google_init"),
    path("google/callback/", views.GoogleAuthCallbackView.as_view(), name="google_callback"),

    path("auth/facebook/", views.FacebookLoginRedirectView.as_view(), name="facebook_login"),
    path("auth/facebook/callback/", views.FacebookCallbackView.as_view(), name="facebook_callback"),

    # jwt refresh
    path('token-refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    #cookies
    path('token/', views.CookieTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', views.CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('token/delete/', views.CookiesTokenDeleteView.as_view(), name='token_delete'),

    path("token/google/", views.CookieGoogleLoginView.as_view(), name="cookie-google-login"),
    path("token/facebook/", views.CookieFacebookLoginView.as_view(), name="cookie-facebook-login"),
]