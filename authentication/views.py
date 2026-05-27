from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import requests, secrets, urllib.parse
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str, force_bytes
from django.contrib.auth import login, logout
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from django.shortcuts import redirect
from django.views import View
from django.http import HttpResponseBadRequest, JsonResponse

from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
import random
from .utils import renew_session, send_verification_email

from .models import TwoFactorCode, EmailVerificationCode
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer,
    CustomTokenObtainPairSerializer, ChangePasswordSerializer,
    ResetPasswordRequestSerializer, ResetPasswordConfirmSerializer,
    TwoFactorRequestSerializer, TwoFactorVerifySerializer, EmailOTPVerifySerializer
)
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from datetime import timedelta
from django.conf import settings


User = get_user_model()


class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer

    def perform_create(self, serializer):
        user = serializer.save()

        # Send OTP email
        send_verification_email(user)

class VerifyEmailOTPView(APIView):
    serializer_class = EmailOTPVerifySerializer

    def post(self, request):
        serializer = EmailOTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"detail": "Invalid email"}, status=status.HTTP_400_BAD_REQUEST)

        record = EmailVerificationCode.objects.filter(user=user, code=code).first()
        if not record:
            return Response({"detail": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)

        # OTP is valid → activate user
        user.verified_email = True
        user.account_status = "active"
        user.save()

        # Delete used OTP
        record.delete()

        return Response({"detail": "Email verified successfully!"}, status=status.HTTP_200_OK)



class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            print("Login error:", e)
            if "email_not_verified" in str(e):
                user = User.objects.filter(email=request.data.get("email")).first()
                send_verification_email(user)
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print("Unexpected error:", e)
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.user

        if user.two_step_verification:
            return Response({'two_factor_required': True}, status=status.HTTP_200_OK)

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")  # Get from cookie

        if not refresh_token:
            return Response(
                {"detail": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

            # Clear the refresh cookie
            response = Response(
                {"detail": "Logged out successfully"},
                status=status.HTTP_200_OK
            )
            response.delete_cookie("refresh_token")
            return response

        except TokenError:
            return Response(
                {"detail": "Invalid or expired token"},
                status=status.HTTP_400_BAD_REQUEST
            )


User = get_user_model()


class GoogleAuthInitView(View):
    """Redirects user to Google OAuth page."""
    def get(self, request):
        state = secrets.token_urlsafe(32)
        request.session["oauth_state"] = state

        params = {
            "client_id": settings.GOOGLE_OAUTH2_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_OAUTH2_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }

        google_url = (
            "https://accounts.google.com/o/oauth2/v2/auth?"
            + urllib.parse.urlencode(params)
        )
        return redirect(google_url)

class GoogleAuthCallbackView(View):
    def get(self, request):
        # 1. Validate state
        state = request.GET.get("state")
        if state != request.session.get("oauth_state"):
            return HttpResponseBadRequest("Invalid state")

        # If Google returns an error
        error = request.GET.get("error")
        if error:
            # Option 1: Redirect back to login page with a message
            return redirect("/login/?error=google_access_denied")

        code = request.GET.get("code")
        if not code:
            return HttpResponseBadRequest("Missing authorization code")


        # 2. Exchange code for tokens
        token_resp = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_OAUTH2_CLIENT_ID,
                "client_secret": settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_OAUTH2_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )

        token_data = token_resp.json()
        id_token_jwt = token_data.get("id_token")
        access_token_google = token_data.get("access_token")

        if not id_token_jwt:
            return HttpResponseBadRequest("Missing ID token")

        # 3. Verify Google ID token
        try:
            id_info = id_token.verify_oauth2_token(
                id_token_jwt,
                google_requests.Request(),
                settings.GOOGLE_OAUTH2_CLIENT_ID,
            )
        except Exception as e:
            return HttpResponseBadRequest(f"ID token validation error: {str(e)}")

        email = id_info.get("email")
        name = id_info.get("name").split(" ")
        picture = id_info.get("picture")

        first_name = name[0] if len(name) > 0 else ""
        last_name = name[1] if len(name) > 1 else ""

        if not email:
            return HttpResponseBadRequest("Email not returned")

        # 4. Create or get the user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={"first_name": first_name, "last_name": last_name},
        )

        print(f"------------User with email {email} {'created' if created else 'retrieved'}. {first_name} {last_name} -----------")
        print(picture)

        if created:
            user.is_active = True

        user.set_unusable_password()
        user.save()

        # 5. Login user using Django session
        login(request, user)

        # 6. Generate SimpleJWT tokens manually
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)

        # 7. redirect to dashboard
        response = redirect("/dashboard")

        # 8. Store refresh in HttpOnly cookie (same as your login code)
        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            samesite="Lax",
            max_age=86400,
            path="/api/auth/token/refresh/",
        )

        return response

class FacebookLoginRedirectView(View):
    def get(self, request):
        fb_auth_url = "https://www.facebook.com/v18.0/dialog/oauth"
        params = {
            "client_id": settings.FACEBOOK_CLIENT_ID,
            "redirect_uri": settings.FACEBOOK_REDIRECT_URI,
            "state": "secure-random-state-value",
            "scope": "email public_profile"
        }

        url = f"{fb_auth_url}?{urllib.parse.urlencode(params)}"
        return redirect(url)

class FacebookCallbackView(View):

    def get(self, request):
        # Check if user denied permissions
        error = request.GET.get("error")
        if error:
            # Option 1: redirect back to login with a message
            return redirect("/login/?error=facebook_access_denied")

        # Get authorization code
        code = request.GET.get("code")
        state = request.GET.get("state")

        if not code:
            return HttpResponseBadRequest("Missing code parameter")

        # Exchange code for access token
        token_url = "https://graph.facebook.com/v18.0/oauth/access_token"

        token_params = {
            "client_id": settings.FACEBOOK_APP_ID,
            "client_secret": settings.FACEBOOK_APP_SECRET,
            "redirect_uri": settings.FACEBOOK_REDIRECT_URI,
            "code": code,
        }

        token_res = requests.get(token_url, params=token_params).json()

        access_token = token_res.get("access_token")
        if not access_token:
            return HttpResponseBadRequest("Unable to get access token")

        # Fetch user profile
        profile_url = "https://graph.facebook.com/me"
        profile_params = {
            "fields": "id,name,email,picture.type(large)",
            "access_token": access_token,
        }

        fb_user = requests.get(profile_url, params=profile_params).json()

        email = fb_user.get("email")
        name = fb_user.get("name").split(" ")
        avatar = fb_user.get("picture", {}).get("data", {}).get("url")

        first_name = name[0] if len(name) > 0 else ""
        last_name = name[1] if len(name) > 1 else ""

        if not email:
            return HttpResponseBadRequest("Facebook account has no email")

        # Create or get user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={"first_name": first_name, "full_name": last_name},
        )

        print(f"------------User with email {email} {'created' if created else 'retrieved'}. {first_name} {last_name} -----------")
        print(avatar)

        if created:
            user.is_active = True
            
        user.set_unusable_password()
        user.save()

        # Log the user in via Django session
        login(request, user)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)

        # Store refresh token in cookie
        response = redirect("/dashboard/")   # Where to redirect after login
        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            samesite="Lax",
            max_age=86400,
            path="/api/auth/token/refresh/"
        )

        return response

class UpdatePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    model = User
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            if not self.object.check_password(serializer.data.get("old_password")):
                return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)

            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            return Response({"detail": "Password updated successfully."})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordRequestView(generics.GenericAPIView):
    serializer_class = ResetPasswordRequestSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = User.objects.filter(email=email).first()
        if user:
            token = PasswordResetTokenGenerator().make_token(user)
            uid = urlsafe_base64_encode(force_str(user.pk).encode())
            # Send email (replace with your frontend reset link)
            reset_link = f"http:{settings.DOMAIN}/reset-password/{uid}/{token}/"
            send_mail("Reset your password", f"Click here to reset: {reset_link}", "demomailtrap.co", [email])

            print("Reset your password", f"Click here to reset: {reset_link}", "demomailtrap.co", [email])

        return Response({"detail": "If an account with that email exists, a reset link has been sent."})


class ResetPasswordConfirmView(generics.GenericAPIView):
    serializer_class = ResetPasswordConfirmSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password has been reset successfully."})


class TwoFactorRequestView(generics.GenericAPIView):
    serializer_class = TwoFactorRequestSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = User.objects.filter(email=email).first()
        if user:
            code = str(random.randint(100000, 999999))
            TwoFactorCode.objects.create(user=user, code=code)
            send_mail("Your verification code",f"Use this code to login: {code}", settings.DEFAULT_FROM_EMAIL, [email])
            print("Your verification code", f"Use this code to login: {code}", settings.DEFAULT_FROM_EMAIL, [email])
        return Response({"detail": "If the email is valid, a verification code has been sent."})


class TwoFactorVerifyView(generics.GenericAPIView):
    serializer_class = TwoFactorVerifySerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = CustomTokenObtainPairSerializer.get_token(user)
        return Response({
            'refresh': str(token),
            'access': str(token.access_token)
        })


# expermenting with JWT token refresh   
from django.contrib.auth import login

class CookieTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # Call DRF SimpleJWT's default behavior first
        response = super().post(request, *args, **kwargs)

        # Get tokens
        refresh = response.data.get("refresh")
        access = response.data.get("access")

        # Get authenticated user from serializer
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user   # <-- authenticated User instance

        # Create Django session login
        login(request, user)

        # Store refresh token in cookie
        if refresh:
            response.set_cookie(
                key="refresh_token",
                value=refresh,
                httponly=True,
                samesite="Lax",
                max_age=86400,
                path="/api/auth/token/refresh/"
            )

        return response

class CookieTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            logout(request)  # logout session if exists
            return Response(
                {"detail": "No refresh token provided"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Inject the cookie refresh token into request data
        request.data['refresh'] = refresh_token

        # Call original TokenRefreshView
        response = super().post(request, *args, **kwargs)

        # 🔥 If refresh FAILED → logout user + delete cookie
        if response.status_code == 401:
            logout(request)

            failed_response = Response(
                {"detail": "Invalid or expired refresh token"},
                status=status.HTTP_401_UNAUTHORIZED
            )

            # Remove invalid/expired cookie
            failed_response.delete_cookie("refresh_token", path="/")

            return failed_response

        # 🔥 If refresh SUCCEEDED → add custom claims
        if response.status_code == 200 and 'access' in response.data:
            try:
                access = AccessToken(response.data['access'])
                user = self.get_user_from_refresh(refresh_token)

                # custom claims
                access['user_id'] = user.id
                access['email'] = user.email
                access['role'] = user.role
                access['status'] = user.user_profile.status
                access['avatar_url'] = user.user_profile.avatar.url if user.user_profile.avatar else None
                access['first_name'] = user.first_name
                access['last_name'] = user.last_name

                response.data['access'] = str(access)
            except Exception as e:
                print("Error attaching custom claims on refresh:", e)

        # Renew Django session (if your logic does that)
        renew_session(request)

        return response

    def get_user_from_refresh(self, refresh_token):
        try:
            refresh = RefreshToken(refresh_token)
            user_id = refresh['user_id']
            return User.objects.get(id=user_id)
        except:
            return None


class CookiesTokenDeleteView(APIView):
    def post(self, request):
        # 1. Blacklist refresh token (JWT logout)
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                pass  # ignore invalid/expired tokens

        # 2. Destroy Django session (template logout)
        logout(request)

        # 3. Build response
        response = Response(
            {"detail": "Logged out successfully"},
            status=status.HTTP_200_OK
        )

        # 4. Delete refresh cookie
        response.delete_cookie(
            key="refresh_token",
            path="/api/auth/token/refresh/"
        )

        return response


class CookieGoogleLoginView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        id_token_value = request.data.get("id_token")
        if not id_token_value:
            return JsonResponse({"error": "id_token is required"}, status=400)

        try:
            google_user = id_token.verify_oauth2_token(
                id_token_value,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )
            email = google_user.get("email")
            first_name = google_user.get("given_name", "")
            last_name = google_user.get("family_name", "")
        except Exception:
            return JsonResponse({"error": "Invalid or expired Google token"}, status=400)

        user, created = User.objects.get_or_create(
            email=email,
            defaults={"first_name": first_name, "last_name": last_name}
        )

        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)

        # Set refresh token in HttpOnly cookie
        response = JsonResponse({
            "access": access,
            "user_id": user.id
        })
        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=False,  # True in production (HTTPS)
            samesite="Lax",
            max_age=86400,       # 1 day
            path="/api/auth/token/refresh/"
        )

        return response
    
class CookieFacebookLoginView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        access_token_value = request.data.get("access_token")
        if not access_token_value:
            return JsonResponse({"error": "access_token is required"}, status=400)

        url = f"https://graph.facebook.com/me?fields=id,name,email&access_token={access_token_value}"
        request = requests.get(url)
        data = request.json()

        if "error" in data:
            return JsonResponse({"error": "Invalid or expired Facebook token"}, status=400)

        email = data.get("email")
        name = data.get("name", "").split(" ")
        first_name = name[0] if len(name) > 0 else ""
        last_name = name[1] if len(name) > 1 else ""

        if not email:
            return JsonResponse({"error": "Facebook account has no email"}, status=400)

        user, created = User.objects.get_or_create(
            email=email,
            defaults={"first_name": first_name, "last_name": last_name}
        )

        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)

        response = JsonResponse({
            "access": access,
            "user_id": user.id
        })
        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=False,  # True in production
            samesite="Lax",
            max_age=86400,       # 1 day
            path="/api/auth/token/refresh/"
        )

        return response
    