"""Canonical subscription feature keys and Pro-detection helpers."""
from django.db.models import Exists, OuterRef
from django.utils import timezone

from .models import Subscription
from .subscription_engine import get_active_subscription, get_remaining_for_feature

# ---- Freelancer Pro perks ----
FEATURED_PROFILE = "featured_profile"     # boolean: badge + boosted in directory
PROFILE_VIEWERS = "profile_viewers"       # boolean: see who viewed my profile
EARLY_ACCESS = "early_access"             # boolean: see new jobs before free users
SEARCH_BOOST = "search_boost"             # boolean: rank above free freelancers
PRIORITY_SUPPORT = "priority_support"     # boolean: shared with employers

# ---- Employer Pro perks ----
FEATURED_JOB = "featured_job"             # numeric: featured job posts per cycle
DIRECT_OFFERS = "offers"                  # existing key used by the offers app
PREMIUM_BADGE = "premium_badge"           # boolean
HIRING_ANALYTICS = "hiring_analytics"     # boolean


def has_feature(user, feature_key):
    """Non-raising boolean check. Falls back to the plan's boolean features for
    subscriptions sold before a perk was added to the plan (remaining_features
    is snapshotted at purchase)."""
    if not user or not user.is_authenticated:
        return False
    sub = get_active_subscription(user)
    if not sub:
        return False
    if feature_key in sub.remaining_features:
        allowed, _ = get_remaining_for_feature(user, feature_key)
        return allowed
    return (
        sub.plan is not None
        and sub.plan.features.filter(feature_name=feature_key, is_boolean=True).exists()
    )


def feature_subscription_exists(feature_key, user_ref="user"):
    """Exists() subquery for annotating list querysets, e.g.
    qs.annotate(is_pro=feature_subscription_exists(SEARCH_BOOST))."""
    return Exists(
        Subscription.objects.filter(
            user=OuterRef(user_ref),
            is_active=True,
            end_date__gte=timezone.now(),
            plan__features__feature_name=feature_key,
        )
    )
