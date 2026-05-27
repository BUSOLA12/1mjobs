from django.utils import timezone
from django.db import transaction as db_transaction
from datetime import timedelta

from .models import Order, Subscription, PlanFeature


def create_subscription_from_order(order_id):
    """
    Given a paid order id, create a Subscription instance.
    - Copies plan features into remaining_features.
    - Sets billing cycle duration (30 days monthly, 365 days yearly).
    - Deactivates any currently active subscriptions for the user (business decision).
    """
    order = Order.objects.select_related("user", "plan").get(pk=order_id)

    # Safety checks
    if order.status != "paid":
        raise ValueError("Order must be paid to create subscription.")

    plan = order.plan
    billing_cycle = order.billing_cycle

    # Compute start/end
    start = timezone.now()
    if billing_cycle == "monthly":
        end = start + timedelta(days=30)
    else:
        end = start + timedelta(days=365)

    # Build remaining_features dict
    features = {}
    for pf in plan.features.all():
        # For boolean features we want True if included
        if pf.is_boolean:
            features[pf.feature_name] = True
        else:
            # If limit is None => unlimited -> store None
            features[pf.feature_name] = pf.limit

    with db_transaction.atomic():
        # Deactivate existing overlapping subscriptions (business choice).
        Subscription.objects.filter(
            user=order.user,
            is_active=True
        ).update(is_active=False)

        sub = Subscription.objects.create(
            user=order.user,
            plan=plan,
            order=order,
            billing_cycle=billing_cycle,
            start_date=start,
            end_date=end,
            remaining_features=features,
            is_active=True
        )

    return sub
