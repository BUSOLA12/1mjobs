from django.db import models
from django.contrib.auth import get_user_model
from ManageJobsTasks.models import Job, Task  # adjust based on your app

User = get_user_model()

# Create your models here.
class Payment(models.Model):

    STATUS_CHOICES = [
        ("NOT_INITIATED", "Not Initiated"),
        ("INITIATED", "Initiated"),
        ("PROCESSING", "Processing"),
        ("ESCROWED", "Escrowed"),
        ("RELEASED", "Released"),
        ("FAILED", "Failed"),
    ]

    employer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments_made")
    freelancer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments_received")

    # Link to your Job/Task model
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="payments")

    amount = models.DecimalField(max_digits=12, decimal_places=2)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="NOT_INITIATED")

    payment_reference = models.CharField(max_length=255, unique=True, null=True, blank=True)

    payment_url = models.URLField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.task.title} - {self.amount} - {self.status}"

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="wallet")
    available_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pending_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} Wallet"

class Transaction(models.Model):
    TRANSACTION_TYPE = (
        ('CREDIT', 'Credit'),
        ('DEBIT', 'Debit'),
    )

    STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions")
    payment = models.ForeignKey("Payment", on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE)
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    reference = models.CharField(max_length=255, unique=True)
    metadata = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
class BankAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bank_accounts")

    account_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=20)
    bank_name = models.CharField(max_length=100)
    bank_code = models.CharField(max_length=20)

    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.account_name} - {self.bank_name}"


from django.db import models
from django.contrib.auth import get_user_model
from ManageJobsTasks.models import Task  # adjust based on your app

User = get_user_model()


class Escrow(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="escrows")
    employer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="employer_escrows")
    freelancer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="freelancer_escrows")

    amount = models.DecimalField(max_digits=12, decimal_places=2)

    is_funded = models.BooleanField(default=False)
    is_released = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Escrow for {self.task.title}"