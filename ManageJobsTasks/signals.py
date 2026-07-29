from notifications.utils import create_notification
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Job, Task, JobApplication, TaskBidding

User = get_user_model()

@receiver(post_save, sender=Job)
def use_create_notification_Job(sender, instance, created, **kwargs):
    if created:
        create_notification(
            title='Job creation notification',
            message=f'A new job ({instance.title}) has been posted. Check it out.',
            related_object=instance
        )


@receiver(post_save, sender=Task)
def use_create_notification_Task(sender, instance, created, **kwargs):
    if created:
        create_notification(
            title='Task creation notification',
            message=f'A new Task ({instance.project_name}) has been posted. Check it out.',
            related_object=instance
        )


@receiver(post_save, sender=JobApplication)
def use_create_notification_Job_Application(sender, instance, created, **kwargs):
    if created:
        create_notification(
            title='Job application notification',
            message=f'{instance.user.first_name} applied for the job ({instance.job.title}).',
            recipient=instance.job.user,
            related_object=instance
        )


@receiver(post_save, sender=TaskBidding)
def use_create_notification_Task_Bidding(sender, instance, created, **kwargs):
    if created:
        create_notification(
            title='New bid notification',
            message=f'{instance.freelancer.first_name} placed a bid of ₦{instance.bid_amount} on your task ({instance.task.project_name}).',
            recipient=instance.task.user,
            related_object=instance
        )