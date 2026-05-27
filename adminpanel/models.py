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
        related_name="admin_target_logs"
    )
    action = models.CharField(max_length=255)  # e.g. Suspend/Ban/Update Profile
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)

    def __str__(self):
        return f"{self.admin} → {self.target_user} : {self.action}"

