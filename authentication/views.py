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
from rest_framework.exceptions import PermissionDenied, AuthenticationFailed
from rest_framework import serializers
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.http import HttpResponseBadRequest, JsonResponse

from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
import random
from .utils import renew_session

from .models import TwoFactorCode, EmailVerificationCode
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer,
    CustomTokenObtainPairSerializer, ChangePasswordSerializer,
    ResetPasswordRequestSerializer, ResetPasswordConfirmSerializer,
    TwoFactorRequestSerializer, TwoFactorVerifySerializer, EmailOTPVerifySerializer,
    TwoFactorConfirmSerializer, AppealSerializer,
    AppealLinkRequestSerializer, AppealTokenSerializer, OTP_VALIDITY_MINUTES
)
from users.models import Appeal
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from datetime import timedelta
from django.utils import timezone
from django.conf import settings


def send_two_factor_code(user):
    """Issue a fresh one-time login/confirmation code and email it to the user.

    Any previously issued, still-unused codes for the user are invalidated first
    so that only the most recent code can be used.
    """
    TwoFactorCode.objects.filter(user=user, is_used=False).update(is_used=True)
    code = str(random.randint(100000, 999999))
    TwoFactorCode.objects.create(user=user, code=code)
    send_mail(
        "Your verification code",
        f"Use this code to continue: {code}\n\nThis code expires in {OTP_VALIDITY_MINUTES} minutes.",
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
    )
    return code


User = get_user_model()


class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer

    def perform_create(self, serializer):
        serializer.save()

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
        except PermissionDenied as e:
            # Suspended/banned account: return the structured block payload so
            # the frontend can redirect to the appeal page.
            return Response(e.detail, status=status.HTTP_403_FORBIDDEN)
        except serializers.ValidationError as e:
            print("Login error:", e)
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print("Unexpected error:", e)
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.user

        if user.two_step_verification:
            return Response({'two_factor_required': True}, status=status.HTTP_200_OK)

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


def _record_appeal(user, message):
    """Create an appeal for a blocked user and notify the admin inbox.

    Returns a DRF Response on any precondition failure (active account or an
    existing pending appeal), or None on success so the caller can return its
    own success payload.
    """
    if not (user.is_banned or user.account_status in ["suspended", "banned"]):
        return Response(
            {"detail": "Your account is active. No appeal is needed."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if Appeal.objects.filter(user=user, status="pending").exists():
        return Response(
            {"detail": "You already have an appeal under review."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    Appeal.objects.create(
        user=user, account_status=user.account_status, message=message
    )
    try:
        send_mail(
            "New account appeal",
            f"{user.email} ({user.account_status}) submitted an appeal:\n\n{message}",
            settings.DEFAULT_FROM_EMAIL,
            [settings.DEFAULT_FROM_EMAIL],
        )
    except Exception as e:
        print("Appeal notification email failed:", e)
    return None


class AppealView(APIView):
    """Let a suspended/banned user submit an appeal. The account owner is
    verified by re-checking the password, since no session exists for a
    blocked user. Passwordless (Google) accounts use AppealLinkRequestView /
    AppealTokenView instead."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AppealSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        message = serializer.validated_data["message"]

        user = User.objects.filter(email=email).first()
        if not user or not user.check_password(password):
            raise AuthenticationFailed("Invalid email or password")

        failure = _record_appeal(user, message)
        if failure is not None:
            return failure

        return Response(
            {"detail": "Your appeal has been submitted. Our team will review it."},
            status=status.HTTP_201_CREATED,
        )


class AppealLinkRequestView(APIView):
    """Email a tokenized appeal link to a blocked user. Used by passwordless
    (Google) accounts that cannot verify ownership with a password. Always
    returns a generic response so account state is never revealed."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AppealLinkRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        user = User.objects.filter(email=email).first()
        if user and _is_blocked(user):
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            query = _blocked_query(user)
            query.update({"uid": uid, "token": token})
            link = request.build_absolute_uri(
                f"{reverse('account_suspended')}?{urllib.parse.urlencode(query)}"
            )
            send_mail(
                "Appeal your account restriction",
                f"Hello,\n\nUse the link below to appeal the restriction on your "
                f"account. The link expires in a few days.\n\n{link}\n\n"
                f"If you did not request this, you can ignore this email.\n\n"
                f"Thank you,\nOne Million Jobs",
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=True,
            )

        return Response(
            {"detail": "If your account is eligible, an appeal link has been sent to your email."}
        )


class AppealTokenView(APIView):
    """Submit an appeal using the tokenized link from AppealLinkRequestView,
    for accounts with no usable password."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AppealTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.validated_data["message"]

        try:
            uid = force_str(urlsafe_base64_decode(serializer.validated_data["uid"]))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"detail": "Invalid or expired appeal link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not default_token_generator.check_token(user, serializer.validated_data["token"]):
            return Response(
                {"detail": "Invalid or expired appeal link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        failure = _record_appeal(user, message)
        if failure is not None:
            return failure

        return Response(
            {"detail": "Your appeal has been submitted. Our team will review it."},
            status=status.HTTP_201_CREATED,
        )


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


def _is_blocked(user):
    """True if the account is suspended or banned (mirrors the password-login gate)."""
    return user.is_banned or user.account_status in ("suspended", "banned")


def _blocked_query(user):
    """Query params for the /account-suspended/ page (used by the Google redirect
    flow, which can't hand JSON to the frontend)."""
    is_banned = user.is_banned or user.account_status == "banned"
    return {
        "status": "banned" if is_banned else "suspended",
        "reason": (user.banned_reason if is_banned else user.suspension_reason) or "",
        "until": user.suspended_until.isoformat() if user.suspended_until else "",
        "email": user.email,
    }


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

        # Block suspended/banned accounts, matching the password-login gate.
        # Only an existing account can be blocked; a freshly created one is active.
        if not created and _is_blocked(user):
            params = urllib.parse.urlencode(_blocked_query(user))
            return redirect(f"/account-suspended/?{params}")

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
            # Google/social accounts have no usable password — skip old password check
            if self.object.has_usable_password():
                old_password = serializer.data.get("old_password", "")
                if not old_password:
                    return Response({"old_password": ["Current password is required."]}, status=status.HTTP_400_BAD_REQUEST)
                if not self.object.check_password(old_password):
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
            # Build the link from the current request so the token is always validated
            # by the same instance that issued it (same SECRET_KEY + database). Hardcoding
            # the host breaks resets when the email is generated on a different instance.
            reset_path = reverse('reset-password', kwargs={'uid': uid, 'token': token})
            reset_link = request.build_absolute_uri(reset_path)
            send_mail("Reset your password", f"Click here to reset: {reset_link}", settings.DEFAULT_FROM_EMAIL, [email])

            print("Password reset link for", email, ":", reset_link)

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
            send_two_factor_code(user)
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


class TwoFactorEnableRequestView(APIView):
    """Send a confirmation code to the logged-in user's email so they can prove
    they control the inbox before two-factor authentication is switched on."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        send_two_factor_code(request.user)
        return Response({"detail": "A confirmation code has been sent to your email."})


class TwoFactorEnableConfirmView(generics.GenericAPIView):
    """Verify the confirmation code, then enable two-factor for the user."""
    serializer_class = TwoFactorConfirmSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data['code'].strip()

        tf = (
            TwoFactorCode.objects
            .filter(user=request.user, code=code, is_used=False)
            .order_by('-created_at')
            .first()
        )
        if not tf:
            return Response({"detail": "Invalid code"}, status=status.HTTP_400_BAD_REQUEST)
        if tf.created_at < timezone.now() - timedelta(minutes=OTP_VALIDITY_MINUTES):
            return Response(
                {"detail": "Code has expired. Please request a new one."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tf.is_used = True
        tf.save(update_fields=["is_used"])

        request.user.two_step_verification = True
        request.user.save(update_fields=["two_step_verification"])
        return Response({"detail": "Two-factor authentication enabled."})


class TwoFactorDisableView(APIView):
    """Turn off two-factor authentication for the logged-in user."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.two_step_verification = False
        request.user.save(update_fields=["two_step_verification"])
        return Response({"detail": "Two-factor authentication disabled."})


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
                settings.GOOGLE_OAUTH2_CLIENT_ID
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

        # Block suspended/banned accounts, matching the password-login gate.
        if not created and _is_blocked(user):
            return JsonResponse(
                CustomTokenObtainPairSerializer._blocked_payload(user), status=403
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
    
    