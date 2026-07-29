from django.core.management.base import BaseCommand
from django.utils import timezone

from ManageJobsTasks.models import Job, Task


class Command(BaseCommand):
    help = "Mark jobs and tasks whose expiration_date has passed as expired."

    def handle(self, *args, **options):
        now = timezone.now()

        # Bulk UPDATEs: one query each, no per-row save(), no signals, and
        # updated_at is intentionally left untouched.
        job_count = Job.objects.filter(
            is_expired=False, expiration_date__lt=now
        ).update(is_expired=True, is_active=False)

        task_count = Task.objects.filter(
            is_expired=False, expiration_date__lt=now
        ).update(is_expired=True, status='expired')

        self.stdout.write(self.style.SUCCESS(
            f"Expired {job_count} job(s) and {task_count} task(s)."
        ))
