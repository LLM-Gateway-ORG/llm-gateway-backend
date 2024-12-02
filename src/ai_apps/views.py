from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Apps
from .serializers import AppSerializer


class AppsViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing App instances.
    """

    serializer_class = AppSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return the Apps related to the authenticated user.
        """
        return Apps.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        Automatically associate the app with the logged-in user during creation.
        """
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Custom create method to ensure the app name is unique for the user
        and handle response formatting.
        """
        app_name = request.data.get("name")
        if Apps.objects.filter(name=app_name, user=request.user).exists():
            return Response(
                {
                    "detail": f"An app with the name '{app_name}' already exists for this user."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        supported_models = request.data.get("supported_models", [])
        # Optional validation for allowed models
        allowed_models = ["GPT-3.5", "GPT-4", "CustomModel"]
        invalid_models = [
            model for model in supported_models if model not in allowed_models
        ]
        if invalid_models:
            return Response(
                {
                    "detail": f"Unsupported models: {', '.join(invalid_models)}. "
                    f"Allowed models are: {', '.join(allowed_models)}."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def update(self, request, *args, **kwargs):
        """
        Custom update method to restrict updates to owned Apps.
        """
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        if instance.user != request.user:
            return Response(
                {"detail": "You do not have permission to edit this app."},
                status=status.HTTP_403_FORBIDDEN,
            )

        supported_models = request.data.get("supported_models", [])
        allowed_models = ["GPT-3.5", "GPT-4", "CustomModel"]
        invalid_models = [
            model for model in supported_models if model not in allowed_models
        ]
        if invalid_models:
            return Response(
                {
                    "detail": f"Unsupported models: {', '.join(invalid_models)}. "
                    f"Allowed models are: {', '.join(allowed_models)}."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)
