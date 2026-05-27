from ..models import AdminActionLog

def log_admin_action(admin, target_user, action, details=""):
    AdminActionLog.objects.create(
        admin=admin,
        target_user=target_user,
        action=action,
        details=details
    )
