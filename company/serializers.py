from rest_framework import serializers
from .models import Company


class CreateCompanySerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()
    documents_url = serializers.SerializerMethodField()
    verified = serializers.SerializerMethodField()
    # Employer Pro premium badge: shown on every job card via company_info.
    is_pro = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at', 'logo_url', 'documents_url', 'verified', 'is_pro')

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

    def get_verified(self, obj):
        return obj.verified

    def get_is_pro(self, obj):
        from pricing.features import PREMIUM_BADGE, has_feature
        return has_feature(obj.created_by, PREMIUM_BADGE)