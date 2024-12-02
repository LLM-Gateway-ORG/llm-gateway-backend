from rest_framework import serializers
from .models import Apps, AppUsers


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
        allowed_models = [
            "GPT-3.5",
            "GPT-4",
            "CustomModel",
        ]  # Define allowed model names
        invalid_models = [model for model in value if model not in allowed_models]

        if invalid_models:
            raise serializers.ValidationError(
                f"Unsupported models: {', '.join(invalid_models)}. "
                f"Allowed models are: {', '.join(allowed_models)}."
            )
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
