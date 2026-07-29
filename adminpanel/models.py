from django.db import models
from django.conf import settings

class AdminActionLog(models.Model):
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name="admin_actions"
    )
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="admin_target_logs",
        null=True,
        blank=True,
    )
    # When the target is not a user (Order, Subscription, Plan, Task, ...),
    # we keep a human-readable label and its type here instead.
    target_repr = models.CharField(max_length=255, blank=True)
    target_type = models.CharField(max_length=50, blank=True)
    action = models.CharField(max_length=255)  # e.g. Suspend/Ban/Update Profile
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)

    @property
    def target_label(self):
        """What to show in the 'Target' column, whoever/whatever the target is."""
        if self.target_user_id:
            return self.target_user.email
        return self.target_repr or "-"

    def __str__(self):
        return f"{self.admin} → {self.target_label} : {self.action}"

