from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import AdminProfile, MessageContact
from .serializers import MessageContactViewSerializer
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes, authentication_classes


# Create your views here.
class SocialsAPIView(APIView):
    def get(self, request):
        try:
            social = AdminProfile.objects.all()
            data = []
            for s in social:
                data.append({
                    "facebook": s.facebook,
                    "gmail": s.gmail,
                    "linkedin": s.linkedin,
                    "x": s.x
                })
            
            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ContactAPIView(APIView):
    def get(self, request):
        try:
            contact = AdminProfile.objects.all()
            data = []
            for c in contact:
                data.append({
                    "facebook": c.facebook,
                    "gmail": c.gmail,
                    "linkedin": c.linkedin,
                    "x": c.x,
                    "address": c.address,
                    "phone": c.phone,
                    "github": c.github
                })
            
            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def message_contact_view(request):
    try:
        serializer = MessageContactViewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Thank you for your message! We'll get back to you soon.",
                    "data": serializer.data
                }, 
                status=status.HTTP_201_CREATED  
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

        

