from rest_framework import serializers
from .models import ProviderAPIKey


class ProviderAPIKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderAPIKey
        fields = ["id", "provider", "created_at"]
        read_only_fields = ["id", "created_at"]


class ProviderAPIKeyDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderAPIKey
        fields = ["id", "provider", "api_key", "created_at"]
        read_only_fields = ["id", "created_at"]


class ProviderAPIKeyUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderAPIKey
        fields = ["api_key"]
