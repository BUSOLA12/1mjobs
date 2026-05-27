from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import UpdateAPIView
from rest_framework.response import Response
from rest_framework import status
from .models import Notification
from .serializers import NotificationListSerializer
from rest_framework.permissions import IsAuthenticated


class NotificationListView(APIView):
    def get(self, request):
        notifications = Notification.objects.filter(recipient=request.user, is_read=False)
        serializer = NotificationListSerializer(notifications, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class MarkOneNotificationReadView(APIView):
    permission_classes = [IsAuthenticated]
    

    def post(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, recipient=request.user)
        except Notification.DoesNotExist:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        notification.is_read = True
        # notification.unread_count = 0
        notification.save()
        return Response({"message": "Notification marked as read."}, status=status.HTTP_200_OK)

class MarkAllNotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            notifications = Notification.objects.filter(recipient=request.user)

        except Notification.DoesNotExist:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        notifications.update(is_read=True)

        
        return Response({"message": "All notifications marked as read."}, status=status.HTTP_200_OK)