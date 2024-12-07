import json
from rest_framework import serializers
from pydantic import ValidationError
from .models import Apps, AppUsers
from .data_models import SdkConfiguration, WebUiConfiguration
from .enum import FeatureTypeEnum

from provider.utils import get_model_list


class AppSerializer(serializers.ModelSerializer):
    """
    Serializer for the Apps model, handling serialization and validation.
    """

    class Meta:
        model = Apps
        fields = [
            "id",
            "name",
            "feature_type",
            "config",
            "supported_models",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_name(self, value):
        """
        Validate that the app name is unique for the user.
        """
        user = self.context["request"].user
        if Apps.objects.filter(name=value, user=user).exists():
            raise serializers.ValidationError(
                f"An app with the name '{value}' already exists for this user."
            )
        return value

    def validate_supported_models(self, value):
        """
        Validate that the provided supported models are allowed.
        """
        allowed_models = get_model_list()
        invalid_models = [model for model in value if model not in allowed_models]

        if len(invalid_models):
            raise serializers.ValidationError(
                f"Unsupported models: {', '.join(invalid_models)}. "
            )
        return value

    def validate_config(self, value):
        """
        Validate configuration for WebUI or SDK
        """
        config_classes = {
            FeatureTypeEnum.WebUI.value: WebUiConfiguration,
            FeatureTypeEnum.SDK.value: SdkConfiguration,
        }

        feature_type = self.instance.feature_type
        if feature_type in config_classes:
            try:
                return json.loads(config_classes[feature_type](**value).json())
            except ValidationError as e:
                raise serializers.ValidationError(json.loads(e.json()))

        raise serializers.ValidationError(
            {"feature_type_error": "Invalid Feature Type"}
        )

    def validate_feature_type(self, value):
        if value not in FeatureTypeEnum:
            raise serializers.ValidationError("Invalid Feature Type")
        
        # Check if this is an update
        if self.instance:
            # Prevent changes to feature_type during updates
            if value != self.instance.feature_type:
                raise serializers.ValidationError("Feature Type cannot be updated.")
        
        return value


class AppUsersSerializer(serializers.ModelSerializer):
    app = AppSerializer()  # Nested App Serializer

    class Meta:
        model = AppUsers
        fields = [
            "app",
            "auth_provider",
            "email",
            "password",
            "first_name",
            "last_name",
        ]
