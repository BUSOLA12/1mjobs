from rest_framework.views import APIView
from rest_framework.generics import UpdateAPIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from users.models import UserProfile
from django.conf import settings
from django.db.models import Q



from ManageJobsTasks.models import Job, Task
from .models import Conversation, Message, MessageNotification
from .serializer import JobConversationCreateSerializer, TaskConversationCreateSerializer


User = get_user_model()


class JobConversationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            job_id = request.data.get("job_id")
            participants = request.data.get("participants", [])

            # ✅ Ensure participants is always a list of integers
            if isinstance(participants, str):
                participants = [
                    int(pid.strip())
                    for pid in participants.split(",")
                    if pid.strip().isdigit()
                ]
            elif isinstance(participants, list):
                participants = [int(pid) for pid in participants]
            else:
                return Response(
                    {"error": "Participants must be a list or comma-separated string."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ✅ Validate job_id & participants
            if not job_id or not participants:
                return Response(
                    {"error": "Job ID and participants are required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ✅ Ensure the job exists
            job = get_object_or_404(Job, id=job_id)

            # ✅ Ensure all participants exist
            participants_objs = [
                get_object_or_404(User, id=participant_id)
                for participant_id in participants
            ]

            # ✅ Use transaction to avoid duplicate creation
            with transaction.atomic():
                # Check if a conversation already exists with the same job and exact participants
                existing_conversations = Conversation.objects.filter(job=job)
                for conv in existing_conversations:
                    conv_participant_ids = list(conv.participants.values_list("id", flat=True))
                    if sorted(conv_participant_ids) == sorted(participants):
                        serializer = JobConversationCreateSerializer(conv)
                        return Response(serializer.data, status=status.HTTP_200_OK)

                # Otherwise, create a new conversation
                subject = f"Conversation on {job.title} job"
                conversation = Conversation.objects.create(job=job, subject=subject)
                conversation.participants.set(participants_objs)
                
                serializer = JobConversationCreateSerializer(conversation)

                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    


class TaskConversationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            task_id = request.data.get("task_id")
            participants = request.data.get("participants", [])

            # ✅ Ensure participants is always a list of integers
            if isinstance(participants, str):
                participants = [
                    int(pid.strip())
                    for pid in participants.split(",")
                    if pid.strip().isdigit()
                ]
            elif isinstance(participants, list):
                participants = [int(pid) for pid in participants]
            else:
                return Response(
                    {"error": "Participants must be a list or comma-separated string."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ✅ Validate task_id & participants
            if not task_id or not participants:
                return Response(
                    {"error": "Task ID and participants are required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ✅ Ensure the job exists
            task = get_object_or_404(Task, id=task_id)

            # ✅ Ensure all participants exist
            participants_objs = [
                get_object_or_404(User, id=participant_id)
                for participant_id in participants
            ]

            # ✅ Use transaction to avoid duplicate creation
            with transaction.atomic():
                # Check if a conversation already exists with the same job and exact participants
                existing_conversations = Conversation.objects.filter(task=task)
                for conv in existing_conversations:
                    conv_participant_ids = list(conv.participants.values_list("id", flat=True))
                    if sorted(conv_participant_ids) == sorted(participants):
                        serializer = TaskConversationCreateSerializer(conv)
                        return Response(serializer.data, status=status.HTTP_200_OK)

                # Otherwise, create a new conversation
                subject = f"Conversation on {task.project_name} task"
                conversation = Conversation.objects.create(task=task, subject=subject)
                conversation.participants.set(participants_objs)
                serializer = TaskConversationCreateSerializer(conversation)

                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class GetConversationView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):

        user = request.user
        print("Authenticated User:", user.id)
        conversations = (
            Conversation.objects.filter(participants=user).prefetch_related('participants', 'messages').order_by('-updated_at')
        )
        q = request.GET.get('q', '')
        if q:
            conversations.filter(
                Q(participants__first_name__icontains=q) |
                Q(participants__last_name__icontains=q) |
                Q(job__title__icontains=q) |
                Q(task__project_name__icontains=q)
            ).distinct()
        data = []

        for conversation in conversations:
            last_message = conversation.get_last_message()
            other_participant = conversation.get_other_participant(user)
            print(other_participant.id if other_participant else "No other participant")
            data.append({
                "conversation_id": conversation.id,
                "subject": conversation.subject,
                "other_user": {
                    "id": other_participant.id if other_participant else None,  
                    "name": other_participant.first_name if other_participant else "Unknown",
                    "avatar": (
                        "" if hasattr(other_participant, "messaging_profile") and other_participant.messaging_profile else None
                    )
                },
                "last_message": {
                    "content": last_message.content if last_message else "",
                    "timestamp": last_message.timestamp.isoformat() if last_message else None,
                    "is_read": last_message.is_read if last_message else False
                } if last_message else None,
                "unread_count": conversation.messages.filter(
                    recipient=user, is_read=False
                ).count()
            })
        
        return Response({"conversations": data})

    def delete(self, request, pk):
        try:
            conv = Conversation.objects.get(pk=pk)
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation with such id does not exist"}, status=status.HTTP_404_NOT_FOUND)

        # Only a participant may delete the conversation.
        if not conv.participants.filter(id=request.user.id).exists():
            return Response(
                {"error": "You are not a participant in this conversation."},
                status=status.HTTP_403_FORBIDDEN
            )

        conv.delete()
        return Response({"message": "Conversation deleted successfully"}, status=status.HTTP_200_OK)




class MessageView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            # ✅ Get data safely from the request
            #job_id = request.data.get("job_id")
            sender_id = request.data.get("sender")
            recipient_id = request.data.get("recipient")
            conversation_id = request.data.get("conversation_id")
            content = request.data.get("content")

            # ✅ Validate required fields
            if not all([sender_id, recipient_id, conversation_id, content]):
                return Response(
                    {"error": "All fields are required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ✅ Get related objects safely
            #job = get_object_or_404(Job, pk=job_id)
            sender = get_object_or_404(User, pk=sender_id)
            recipient = get_object_or_404(User, pk=recipient_id)
            conversation = get_object_or_404(Conversation, pk=conversation_id)

            # ✅ Create message
            message = Message.objects.create(
                conversation=conversation,
                sender=sender,
                recipient=recipient,
                content=content
            )

            Notification = MessageNotification.objects.create(
                message=message,
                conversation=conversation,
                user=sender
                )

            # ✅ You can return the created message data or success response
            return Response(
                {
                    "message": "Message sent successfully",
                    "data": {
                        "id": message.id,
                        "sender": sender.first_name,
                        "recipient": recipient.first_name,
                        "content": message.content,
                        "conversation_id": conversation.id,
                    }
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    def get(self, request, pk):
        c = Conversation.objects.get(pk=pk)
        message = Message.objects.filter(conversation=c)
        data = []
        for m in message:
            data.append({
                "content": m.content,
                "sender_id": m.sender.id,
                "timestamp": m.timestamp,
                "message_type": m.message_type
            })
        
        return Response({"messages": data})
    
class UnreadNotificationView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        notifications = MessageNotification.objects.filter(is_read=False).select_related(
            "message__sender__user_profile",
            "message__recipient",
            "conversation"
        )
        notc_data = []
        for n in notifications:
            profile = n.message.sender.user_profile
            notc_data.append({
                "user_avatar": f"{settings.BASE_URL}{profile.avatar.url}",
                "sender": n.message.sender.first_name,
                "recipient": n.message.recipient.id,
                "conversation_id": n.conversation.id,
                "sender_id": n.message.sender.id,
                "notification_id": n.id,
                "message": n.message.content,
                "timestamp": n.message.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            })
        return Response({"notifications": notc_data})
    

class MarkOneReadView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = MessageNotification.objects.all()

    def update(self, request, *args, **kwargs):
        notification = self.get_object()
        notification.is_read = True
        notification.unread_count = 0
        notification.save()
        return Response({"message": "Notification marked as read."}, status=status.HTTP_200_OK)

class MarkAllReadView(APIView):
    permission_classes = [IsAuthenticated]
    
    def put(self, request):
        # Notification rows are stored against the message's sender, so the
        # unread items belonging to the requester are those where they are the
        # message recipient (matches UnreadNotificationView's per-user view).
        notifications = MessageNotification.objects.filter(
            message__recipient=request.user, is_read=False
        )
        notifications.update(is_read=True, unread_count=0)
        return Response(
            {"message": "All notifications marked as read."},
            status=status.HTTP_200_OK
        )