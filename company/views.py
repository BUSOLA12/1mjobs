from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import CreateCompanySerializer
from rest_framework.response import Response
from rest_framework import status
from .models import Company

# Create your views here.

class CreateCompanyAPIView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        # Creating a company requires a logged-in user; viewing stays public.
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]

    def post(self, request):
        if Company.objects.filter(created_by=request.user).exists():
            return Response({"Message": "A Company Already Posted By this User"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = CreateCompanySerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response({"Message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        try:
            company = Company.objects.get(created_by=pk)
            serializer = CreateCompanySerializer(company, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)


        except Company.DoesNotExist:
            return Response({"error": "Company not found. Create a company in profile settings"}, status=status.HTTP_404_NOT_FOUND)

class CompanyExistsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            if Company.objects.filter(created_by=pk).exists():
                return Response({"status": True}, status=status.HTTP_200_OK)
            else:
                return Response({"status": False}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"{str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)