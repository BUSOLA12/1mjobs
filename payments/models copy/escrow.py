from django.db import models
from django.contrib.auth import get_user_model
from ManageJobsTasks.models import Job  # adjust based on your app

User = get_user_model()


class Escrow(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="escrows")
    employer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="employer_escrows")
    freelancer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="freelancer_escrows")

    amount = models.DecimalField(max_digits=12, decimal_places=2)

    is_funded = models.BooleanField(default=False)
    is_released = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Escrow for {self.job.title}"