from rest_framework import serializers
from .models import Payment, Wallet, Withdrawal

def _payment_job_title(obj):
    """A payment belongs to either a Task (title = project_name) or a Contract
    (title = the job's title). Handle both, and never crash on a null side."""
    if obj.task_id:
        return obj.task.project_name
    if obj.contract_id:
        return obj.contract.subject_title
    return "Payment"


class PaymentListSerializer(serializers.ModelSerializer):
    job_title = serializers.SerializerMethodField()
    freelancer_name = serializers.CharField(source="freelancer.get_full_name")
    # The payments-page JS reads `payment_status`; keep both for compatibility.
    payment_status = serializers.CharField(source="status")

    class Meta:
        model = Payment
        fields = [
            "id",
            "job_title",
            "freelancer_name",
            "amount",
            "status",
            "payment_status",
            "payment_url",
        ]

    def get_job_title(self, obj):
        return _payment_job_title(obj)

class PaymentDetailSerializer(serializers.ModelSerializer):
    job_title = serializers.SerializerMethodField()
    freelancer_name = serializers.CharField(source="freelancer.get_full_name")
    payment_status = serializers.CharField(source="status")

    class Meta:
        model = Payment
        fields = [
            "id",
            "job_title",
            "freelancer_name",
            "amount",
            "commission_amount",
            "vat_amount",
            "net_amount",
            "status",
            "payment_status",
            "payment_url",
            "created_at",
            "updated_at",
        ]

    def get_job_title(self, obj):
        return _payment_job_title(obj)

class WalletSerializer(serializers.ModelSerializer):

    class Meta:
        model = Wallet
        fields = [
            "available_balance",
            "pending_balance",
        ]


class WithdrawalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Withdrawal
        fields = [
            "id", "amount", "status", "account_name", "account_number",
            "bank_name", "admin_note", "created_at", "processed_at",
        ]
        read_only_fields = fields



# from rest_framework import serializers
# from payments.models import Transaction


# class TransactionSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Transaction
#         fields = "__all__"

# from rest_framework import serializers
# from payments.models import Escrow


# class EscrowSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Escrow
#         fields = "__all__"
#         read_only_fields = ["is_funded", "is_released"]

# from rest_framework import serializers


# class WithdrawalSerializer(serializers.Serializer):
#     amount = serializers.DecimalField(max_digits=12, decimal_places=2)

