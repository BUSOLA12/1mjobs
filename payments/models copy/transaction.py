from django.db import models
from .wallet import Wallet


class Transaction(models.Model):

    TRANSACTION_TYPE = (
        ('funding', 'Funding'),
        ('escrow_funding', 'Escrow Funding'),
        ('release', 'Release'),
        ('withdrawal', 'Withdrawal'),
        ('refund', 'Refund'),
        ('fee', 'Platform Fee'),
    )

    STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE)
    status = models.CharField(max_length=20, choices=STATUS, default='pending')

    reference = models.CharField(max_length=255, unique=True)
    metadata = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.amount}"