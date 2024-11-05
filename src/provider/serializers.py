from rest_framework import serializers
from .models import ProviderAPIKey
from provider.helpers import decrypt_value


class ProviderAPIKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderAPIKey
        fields = ["id", "provider", "created_at"]
        read_only_fields = ["id", "created_at"]


class ProviderAPIKeyDetailsSerializer(serializers.ModelSerializer):
    api_key = serializers.SerializerMethodField()

    class Meta:
        model = ProviderAPIKey
        fields = ["id", "provider", "api_key", "created_at"]
        read_only_fields = ["id", "created_at"]

    def get_api_key(self, obj):
        return decrypt_value(obj.api_key)


class ProviderAPIKeyUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderAPIKey
        fields = ["api_key"]
