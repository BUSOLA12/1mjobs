from django.contrib.auth.decorators import user_passes_test

def admin_required(function):
    decorator = user_passes_test(lambda u: u.is_authenticated and u.role == 'admin')
    return decorator(function)