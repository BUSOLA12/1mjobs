from django.apps import AppConfig


class ManagejobstasksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ManageJobsTasks"

    def ready(self):
        import ManageJobsTasks.signals