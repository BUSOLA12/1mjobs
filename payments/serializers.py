from rest_framework import serializers
from .models import Payment, Wallet

class PaymentListSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="task.title")
    freelancer_name = serializers.CharField(source="freelancer.get_full_name")

    class Meta:
        model = Payment
        fields = [
            "id",
            "job_title",
            "freelancer_name",
            "amount",
            "status",
            "payment_url",
        ]

class PaymentDetailSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="task.title")
    freelancer_name = serializers.CharField(source="freelancer.get_full_name")

    class Meta:
        model = Payment
        fields = [
            "id",
            "job_title",
            "freelancer_name",
            "amount",
            "status",
            "payment_url",
            "created_at",
            "updated_at",
        ]

class WalletSerializer(serializers.ModelSerializer):

    class Meta:
        model = Wallet
        fields = [
            "available_balance",
            "pending_balance",
        ]



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

