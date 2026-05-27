from .models import UserActivityLog

def log_user_action(user, action, user_agent=None, ip_address=None, metadata={}):
    UserActivityLog.objects.create(user=user, action=action, ip_address=ip_address, 
                                   user_agent=user_agent, metadata=metadata)
    