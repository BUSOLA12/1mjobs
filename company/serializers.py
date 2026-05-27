
from rest_framework import serializers
from .models import Company


class CreateCompanySerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()
    documents_url = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at', 'logo_url', 'documents_url')


    def get_logo_url(self, obj):
        request = self.context.get('request')
        if obj.logo and request:
            return request.build_absolute_uri(obj.logo.url)
        return None

    def get_documents_url(self, obj):
        request = self.context.get('request')
        if obj.documents and request:
            return request.build_absolute_uri(obj.documents.url)
        return None