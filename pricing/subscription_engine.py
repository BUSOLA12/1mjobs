from django.utils import timezone
from django.db import transaction as db_transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import Subscription


def get_active_subscription(user):
    """
    Return the most-recent active subscription for the user or None.
    Active = is_active True and end_date >= now
    """
    return (
        Subscription.objects.filter(
            user=user,
            is_active=True,
            end_date__gte=timezone.now()
        ).order_by("-end_date").first()
    )


def get_remaining_for_feature(user, feature_key):
    """
    Return a tuple (allowed: bool, remaining_value_or_none):
      - If allowed and remaining_value is:
         - None => unlimited
         - int => remaining units
         - True => boolean feature present (allowed)
      - If not allowed, returns (False, 0 or None)
    """
    sub = get_active_subscription(user)
    if not sub:
        return False, None

    remaining = sub.remaining_features.get(feature_key)

    # Acceptable values:
    # None -> unlimited (allowed)
    # True -> boolean feature present
    # int -> numeric remaining
    if remaining is None:
        # If key present but set to None, treat as unlimited
        # If key missing entirely, remaining will be None too; treat missing below.
        if feature_key in sub.remaining_features:
            return True, None
    if isinstance(remaining, bool):
        return (True, True) if remaining else (False, 0)
    if isinstance(remaining, int):
        return (remaining > 0), remaining

    # key missing -> not included
    return False, None


def check_feature_allowed(user, feature_key):
    """
    Check whether user is allowed to perform an action (read-only).
    Raises PermissionDenied with a message if not allowed.
    Returns remaining value if allowed (None for unlimited, True for boolean, int otherwise).
    """
    allowed, remaining = get_remaining_for_feature(user, feature_key)
    if not allowed:
        raise PermissionDenied("You do not have an active subscription or this feature is not included / exhausted.")
    return remaining


def check_and_consume_feature(user, feature_key, consume_amount=1):
    """
    Check and consume usage for a feature inside an atomic block.

    - For boolean features (True), this only checks and returns True (no consumption).
    - For unlimited features (None), it just returns True.
    - For numeric features, it decrements by `consume_amount` (default 1) and saves.

    Raises PermissionDenied if not allowed.
    """
    sub = get_active_subscription(user)
    if not sub:
        raise PermissionDenied("You do not have an active subscription.")

    # Ensure atomicity when modifying
    with db_transaction.atomic():
        # re-fetch to lock row (optional micro-optimization)
        sub = Subscription.objects.select_for_update().get(pk=sub.pk)

        if feature_key not in sub.remaining_features:
            raise PermissionDenied("This feature is not included in your plan.")

        current = sub.remaining_features.get(feature_key)

        # Boolean feature - no consumption
        if isinstance(current, bool):
            if current:
                return True
            raise PermissionDenied("This boolean feature is not available in your plan.")

        # Unlimited (None) - allowed, no change
        if current is None:
            return True

        # Numeric
        if isinstance(current, int):
            if current < consume_amount:
                raise PermissionDenied("Your plan limit for this feature has been exhausted.")
            sub.remaining_features[feature_key] = current - consume_amount
            # Save only remaining_features to minimize race surface
            sub.save(update_fields=["remaining_features"])
            return True

        # Fallback - not allowed
        raise PermissionDenied("Invalid feature configuration.")
