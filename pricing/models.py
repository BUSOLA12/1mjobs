from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class Plan(models.Model):
    USER_TYPES = [
        ("freelancer", "Freelancer"),
        ("employer", "Employer"),
    ]

    BILLING_CYCLES = [
        ("monthly", "Monthly"),
        ("yearly", "Yearly"),
    ]

    name = models.CharField(max_length=50)
    user_type = models.CharField(max_length=20, choices=USER_TYPES, db_index=True)
    description = models.TextField(blank=True)

    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)
    yearly_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.user_type})"

class PlanFeature(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="features")

    feature_name = models.CharField(max_length=100)
    limit = models.PositiveIntegerField(null=True, blank=True)  # null = unlimited
    is_boolean = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.plan.name} - {self.feature_name}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    BILLING_CYCLE_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True)
    plan_name_snapshot = models.CharField(max_length=100, blank=True)
    billing_cycle = models.CharField(max_length=10, choices=BILLING_CYCLE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    is_locked = models.BooleanField(default=False)


    def __str__(self):
        return f"Order {self.id} - {self.status}"


class Subscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)

    billing_cycle = models.CharField(max_length=10)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()

    remaining_features = models.JSONField(default=dict)

    is_active = models.BooleanField(default=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.end_date:
            if self.billing_cycle == "monthly":
                self.end_date = self.start_date + timedelta(days=30)
            else:
                self.end_date = self.start_date + timedelta(days=365)

        # If new subscription: load feature limits
        if not self.remaining_features and self.plan:
            self.remaining_features = {
                f.feature_name: f.limit for f in self.plan.features.all()
            }
        super().save(*args, **kwargs)

    def has_expired(self):
        return timezone.now() > self.end_date

    def use_feature(self, feature):
        """Deduct usage from feature limits"""
        value = self.remaining_features.get(feature)

        if value is None:  # unlimited
            return True

        if value > 0:
            self.remaining_features[feature] -= 1
            self.save()
            return True

        return False


    def __str__(self):
        return f"{self.user.email} - {self.plan.name}"


class Transaction(models.Model):
    status_list = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    reference = models.CharField(max_length=100, unique=True)
    authorization_url = models.URLField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=status_list)
    created_at = models.DateTimeField(auto_now_add=True)


