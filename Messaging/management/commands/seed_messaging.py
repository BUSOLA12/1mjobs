# messaging/management/commands/seed_messaging.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from Messaging.models import Conversation, Message, MessageNotification
from ManageJobsTasks.models import Job, Task
from faker import Faker
import random

from django.db.models.signals import post_save
from Messaging import signals as messaging_signals

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    help = "Seed demo conversations, messages, and notifications"
    post_save.disconnect(messaging_signals.notify_unread_messages, sender=Message)
    
    # ... your seeding logic here ...

    def add_arguments(self, parser):
        parser.add_argument('--conversations', type=int, default=5, help='Number of conversations to create')
        parser.add_argument('--messages', type=int, default=10, help='Messages per conversation')

    def handle(self, *args, **options):
        num_conversations = options['conversations']
        num_messages = options['messages']

        users = list(User.objects.all())
        jobs = list(Job.objects.all())
        tasks = list(Task.objects.all())

        if len(users) < 2:
            self.stdout.write(self.style.ERROR("You need at least 2 users to create conversations."))
            return

        created_convos = 0
        created_msgs = 0

        for _ in range(num_conversations):
            # Pick 2 random distinct users
            u1, u2 = random.sample(users, 2)

            # Prevent duplicate conversation
            convo, created = Conversation.objects.get_or_create()
            convo.participants.set([u1, u2])

            # Optionally attach to a job or task
            if jobs and random.choice([True, False]):
                convo.job = random.choice(jobs)
            elif tasks:
                convo.task = random.choice(tasks)
            convo.save()

            if created:
                created_convos += 1

            # Create messages
            for _ in range(num_messages):
                sender, recipient = random.choice([(u1, u2), (u2, u1)])
                msg = Message.objects.create(
                    conversation=convo,
                    sender=sender,
                    recipient=recipient,
                    content=fake.sentence(),
                    message_type='text'
                )
                created_msgs += 1

                # Create notification for recipient
                notif, _ = MessageNotification.objects.get_or_create(
                    user=recipient,
                    conversation=convo,
                    defaults={'unread_count': 0}
                )
                notif.unread_count += 1
                notif.message = msg
                notif.save()

        # Reconnect signals if needed
        post_save.connect(messaging_signals.notify_unread_messages, sender=Message)

        self.stdout.write(self.style.SUCCESS(
            f"✅ Seeded {created_convos} new conversations with {created_msgs} messages."
        ))
