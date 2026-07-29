from django.contrib.auth import get_user_model

from ..models import AdminActionLog


def log_admin_action(admin, target, action, details=""):
    """Record an admin action.

    `target` may be a user (suspend/ban/edit) or any other object the action
    affected (Order, Subscription, Plan, Task, bid, ...). Users go in the FK;
    everything else is stored as a readable label so the log never crashes.
    """
    User = get_user_model()

    if isinstance(target, User):
        return AdminActionLog.objects.create(
            admin=admin,
            target_user=target,
            action=action,
            details=details,
        )

    if target is None:
        target_repr, target_type = "", ""
    else:
        target_type = target.__class__.__name__
        # A broken __str__ on the target must never break the admin action.
        try:
            target_repr = str(target)
        except Exception:
            target_repr = f"{target_type} #{getattr(target, 'pk', '?')}"

    return AdminActionLog.objects.create(
        admin=admin,
        target_user=None,
        target_repr=target_repr,
        target_type=target_type,
        action=action,
        details=details,
    )
