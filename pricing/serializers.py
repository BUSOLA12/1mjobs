from rest_framework import serializers
from .models import Plan, PlanFeature, Order, Subscription


# -------------------------
# PLAN + FEATURES
# -------------------------
class PlanFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanFeature
        fields = ["feature_name", "limit", "is_boolean"]


class PlanSerializer(serializers.ModelSerializer):
    features = PlanFeatureSerializer(many=True, read_only=True)

    class Meta:
        model = Plan
        fields = [
            "id", "name", "user_type", "description",
            "monthly_price", "yearly_price",
            "features"
        ]


# -------------------------
# ORDER
# -------------------------
class OrderSerializer(serializers.ModelSerializer):
    plan = serializers.PrimaryKeyRelatedField(
        queryset=Plan.objects.all(), write_only=True, required=False
    )
    plan_data = PlanSerializer(source="plan", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "user", "plan", "plan_data", "plan_name_snapshot", "billing_cycle",
            "amount", "status", "payment_reference", "created_at"
        ]
        read_only_fields = ["user", "status", "payment_reference", "created_at", "plan_name_snapshot"]

    def validate(self, data):
        """
        Make PATCH safe:
        - If `plan` not included, use instance.plan
        - If `billing_cycle` not included, use instance.billing_cycle
        Prevent KeyError and allow partial updates.
        """
        plan = data.get("plan", getattr(self.instance, "plan", None))
        cycle = data.get("billing_cycle", getattr(self.instance, "billing_cycle", None))

        if plan is None:
            raise serializers.ValidationError("A valid plan is required.")

        if cycle not in ["monthly", "yearly"]:
            raise serializers.ValidationError("Invalid billing cycle.")

        # Validate allowed billing cycles
        if cycle == "monthly" and not plan.monthly_price:
            raise serializers.ValidationError("This plan has no monthly option.")
        if cycle == "yearly" and not plan.yearly_price:
            raise serializers.ValidationError("This plan has no yearly option.")

        return data

    def update(self, instance, validated_data):
        """
        Auto-recalculate the amount when plan or billing_cycle changes.
        """
        plan = validated_data.get("plan", instance.plan)
        cycle = validated_data.get("billing_cycle", instance.billing_cycle)

        # Recalculate amount only if user updates something relevant
        if "plan" in validated_data or "billing_cycle" in validated_data:
            validated_data["amount"] = (
                plan.monthly_price if cycle == "monthly" else plan.yearly_price
            )

        return super().update(instance, validated_data)

    def create(self, validated_data):
        plan = validated_data["plan"]
        cycle = validated_data["billing_cycle"]

        validated_data["plan_name_snapshot"] = plan.name
        validated_data["amount"] = (
            plan.monthly_price if cycle == "monthly" else plan.yearly_price
        )

        return super().create(validated_data)



# -------------------------
# SUBSCRIPTION
# -------------------------
class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    has_expired = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = [
            "id", "plan", "order", "billing_cycle",
            "start_date", "end_date",
            "remaining_features", "is_active",
            "has_expired",
        ]

    def get_has_expired(self, obj):
        return obj.has_expired()
