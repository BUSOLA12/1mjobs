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

    # A payment belongs to EITHER a Task (legacy bid-based flow) OR a Contract
    # (the job/candidate hiring flow). Both are nullable so each path can use the
    # one that applies.
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="payments", null=True, blank=True)
    contract = models.ForeignKey(
        "contracts.Contract", on_delete=models.CASCADE, related_name="payments",
        null=True, blank=True,
    )
    # For recurring (Job) contracts, the specific billing period this escrow
    # payment funds. Null for one-shot (Task) contract payments.
    period = models.ForeignKey(
        "contracts.BillingPeriod", on_delete=models.CASCADE, related_name="payments",
        null=True, blank=True,
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)

    # Filled at release time. The escrowed `amount` splits into:
    #   net_amount (to the freelancer) + commission_amount (platform) + vat_amount (tax).
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="NOT_INITIATED")

    payment_reference = models.CharField(max_length=255, unique=True, null=True, blank=True)

    payment_url = models.URLField(null=True, blank=True)

    # African Money collection id, set at initiation, used for server-side verify
    collection_id = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        subject = self.task.title if self.task_id else (
            self.contract.job.title if self.contract_id else "Payment"
        )
        return f"{subject} - {self.amount} - {self.status}"

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
        ('FEE', 'Platform Fee'),
        ('VAT', 'VAT'),
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


class Withdrawal(models.Model):
    """A freelancer's request to cash out available wallet funds. Processed
    manually by an admin: on 'paid' the wallet available_balance is debited and
    a DEBIT transaction is written. The admin verifies the bank details first."""

    STATUS_CHOICES = [
        ("requested", "Requested"),
        ("approved", "Approved"),
        ("paid", "Paid"),
        ("rejected", "Rejected"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="withdrawals")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    bank_account = models.ForeignKey(
        BankAccount, on_delete=models.SET_NULL, null=True, blank=True, related_name="withdrawals"
    )
    # Snapshot of the bank details at request time (kept even if BankAccount changes).
    account_name = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=20, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="requested")
    admin_note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Withdrawal {self.amount} by {self.user.email} ({self.status})"


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