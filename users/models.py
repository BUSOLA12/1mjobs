from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.conf import settings
from django.db import models
from django.utils import timezone

roles = (
    ('freelancer', 'Freelancer'),
    ('employer', 'Employer'),
    ('admin', 'Admin'),
)

status_choices = (
    ('active', 'Active'),
    ('inactive', 'Inactive'),
)

ACCOUNT_STATUS_CHOICES = [
    ("pending_verification", "Pending Verification"),
    ("active", "Active"),
    ("suspended", "Suspended"),
    ("banned", "Banned"),
]

VERIFICATION_STATUS = [
    ("pending", "Pending"),
    ("verified", "Verified"),
]

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email address is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("verified_email", True)
        extra_fields.setdefault("role", "admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        
        # set user role to admin
        user = self.create_user(email, password, **extra_fields)
        user.role = 'admin'
        user.save(using=self._db)

        return user

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=50, choices=roles, default='freelancer')
    two_step_verification = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    verified_email = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    # Account Control Fields
    account_status = models.CharField(
        max_length=30,
        choices=ACCOUNT_STATUS_CHOICES,
        default="pending_verification"
    )
    suspended_until = models.DateTimeField(null=True, blank=True)
    suspension_reason = models.TextField(blank=True)

    is_banned = models.BooleanField(default=False)
    banned_reason = models.TextField(blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    # ------------------
    # Helper Methods
    # ------------------

    @property
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_suspended(self):
        if self.account_status == "suspended":
            # Auto-unsuspend if time passed
            if self.suspended_until and timezone.now() >= self.suspended_until:
                return False
            return True
        return False

    def suspend(self, days: int = None, until: timezone.datetime = None, reason: str = ""):
        self.account_status = "suspended"
        self.suspension_reason = reason or ""
        self.is_active = False

        if days:
            self.suspended_until = timezone.now() + timezone.timedelta(days=days)
        elif until:
            self.suspended_until = until
        else:
            self.suspended_until = None  # indefinite suspension

        self.save(update_fields=["account_status", "suspended_until", "suspension_reason", "is_active"])

    def unsuspend(self):
        self.account_status = "active"
        self.suspended_until = None
        self.suspension_reason = ""
        self.is_active = True
        self.save(update_fields=["account_status", "suspended_until", "suspension_reason", "is_active"])

    def ban(self, reason: str = ""):
        self.is_banned = True
        self.banned_reason = reason or ""
        self.account_status = "banned"
        self.is_active = False
        self.save(update_fields=["is_banned", "banned_reason", "account_status", "is_active"])

    def unban(self):
        self.is_banned = False
        self.banned_reason = ""
        self.account_status = "active"
        self.is_active = True
        self.save(update_fields=["is_banned", "banned_reason", "account_status", "is_active"])

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_profile')
    avatar = models.ImageField(upload_to='avatars/', default='avatars/user-avatar-placeholder.png')
    bio = models.TextField(blank=True)
    skills = models.ManyToManyField('Skill', blank=True, related_name='profiles')
    tagline = models.CharField(max_length=255, blank=True)
    category = models.ForeignKey("Category", on_delete=models.SET_NULL, null=True, blank=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=50, choices=status_choices, default='active')
    job_success = models.PositiveSmallIntegerField(default=0, help_text="Percentage 0-100")
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=0.0)
    kyc_verified = models.BooleanField(default=False)
    avg_rating = models.FloatField(default=0.0)
    rating_count = models.IntegerField(default=0)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["nationality"]),
            models.Index(fields=["hourly_rate"]),
            models.Index(fields=["rating"]),
            models.Index(fields=["job_success"]),
        ]
        ordering = ["-rating", "-job_success", "hourly_rate"]

    def __str__(self):
        return f"{self.user.email}'s profile"

class UserKYC(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='kyc')
    id_type = models.CharField(max_length=50, blank=True)  # passport, national id etc
    id_number = models.CharField(max_length=120, blank=True)
    id_document = models.FileField(upload_to='kyc/%Y/%m/%d/', null=True, blank=True)
    address_document = models.FileField(upload_to='kyc/address/%Y/%m/%d/', null=True, blank=True)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='pending')
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="kyc_reviewed")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def mark_approved(self, reviewer):
        self.verification_status = "approved"
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save(update_fields=["verification_status", "reviewed_by", "reviewed_at"])
        # reflect on user
        u = self.user
        u.user_profile.kyc_verified = True
        u.save()


class UserActivityLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="activity_logs", null=True, blank=True)
    action = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.action

class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class UserFile(models.Model):
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='file')
    file = models.FileField(upload_to='user_files/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"File for {self.profile.user.email}"

class WorkHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="work_histories")
    company_name = models.CharField(max_length=255)
    work_role = models.CharField(max_length=255)
    start_month_year = models.CharField(max_length=50)
    end_month_year = models.CharField(max_length=50, blank=True, null=True)  # “Present” allowed
    responsibilities = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.work_role} at {self.company_name}"

