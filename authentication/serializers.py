from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from users.models import UserProfile
from rest_framework.exceptions import PermissionDenied, AuthenticationFailed

#JWT imports 
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer, TokenRefreshSerializer
)
from rest_framework_simplejwt.tokens import RefreshToken

#password Reset imports
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_str, smart_bytes, smart_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

# Two-Factor Authentication imports
from .models import TwoFactorCode

# Get the user model
User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'role']

    def create(self, validated_data):
        print("Creating user with data:", validated_data)
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data.get('role', 'freelancer')
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(username=email, password=password)

        if user is None:
            user = User.objects.filter(email=email).first()
            if user:
                if user.is_banned or user.account_status in ["suspended", "banned"]:
                    raise PermissionDenied("Account is suspended or banned")
            raise AuthenticationFailed("Invalid email or password")
        elif user.account_status == "pending_verification" or not user.verified_email:
            raise serializers.ValidationError({
                "detail": "Email not verified.",
                "code": "email_not_verified"
            })


        self.user = user  # store user for get_token use
        data = super().validate(attrs)
        data['user_id'] = user.id
        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['user_id'] = user.id
        token['email'] = user.email
        token['role'] = user.role
        token['status'] = user.user_profile.status
        token['avatar_url'] = user.user_profile.avatar.url if user.user_profile.avatar else None
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        return token

#Password Reset Serializer
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class ResetPasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordConfirmSerializer(serializers.Serializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField()

    def validate(self, attrs):
        try:
            uid = force_str(urlsafe_base64_decode(attrs['uidb64']))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError('Invalid reset link')

        if not PasswordResetTokenGenerator().check_token(user, attrs['token']):
            raise serializers.ValidationError('Invalid or expired token')

        validate_password(attrs['new_password'])
        attrs['user'] = user
        return attrs

    def save(self):
        password = self.validated_data['new_password']
        user = self.validated_data['user']
        user.set_password(password)
        user.save()

#Two-Factor Authentication Serializer

class TwoFactorRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class TwoFactorVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        try:
            user = User.objects.get(email=attrs['email'])
            tf = TwoFactorCode.objects.filter(user=user, code=attrs['code'], is_used=False).latest('created_at')
        except (User.DoesNotExist, TwoFactorCode.DoesNotExist):
            raise serializers.ValidationError("Invalid code")

        attrs['user'] = user
        attrs['tf_code'] = tf
        return attrs

    def save(self):
        self.validated_data['tf_code'].is_used = True
        self.validated_data['tf_code'].save()
        return self.validated_data['user']
    
class EmailOTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
