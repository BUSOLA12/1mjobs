from rest_framework import serializers
from .models import AdminProfile, MessageContact


class MessageContactViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageContact
        fields = '__all__'