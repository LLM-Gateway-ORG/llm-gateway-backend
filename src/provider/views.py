import json

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.http import StreamingHttpResponse, JsonResponse
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response

from authentication.permissions import APIKeyPermission
from provider.models import ProviderAPIKey
from provider.utils import chat_completion
from provider.constants import AI_MODELS
from provider.serializers import (
    ProviderAPIKeySerializer,
    ProviderAPIKeyDetailsSerializer,
    ProviderAPIKeyUpdateSerializer,
)

# Create your views here.


class BaseGenerateCompletionView(APIView):
    def get_permission_classes(self):
        """Override this method in subclasses to set specific permissions."""
        raise NotImplementedError("Subclasses must define permission classes")

    def post(self, request) -> StreamingHttpResponse:
        # Parse request body
        try:
            body = request.data
            messages = body.get("messages", [])
            model_name = body.get("model_name")
            provider_id = body.get("provider_id")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON body"}, status=400)

        # Fetch Provider Details
        provider_list = ProviderAPIKey.objects.filter(id=provider_id, user=request.user)
        if not provider_list.exists():
            return JsonResponse(
                {"error": "Provider Not Found or Access Denied"}, status=400
            )

        provider_obj = provider_list.first()

        # Check Model List
        if not any(
            i["model_name"] == model_name
            and i["provider"].value == provider_obj.provider
            for i in AI_MODELS
        ):
            return JsonResponse({"error": "Model Not Found for Provider"}, status=400)

        # Initialize and load model
        llm = chat_completion(
            api_key=provider_obj.api_key,
            model_name=model_name,
            provider=provider_obj.provider,
        )

        # Define a generator for the StreamingHttpResponse
        async def stream_chat():
            try:
                async for response in llm.chat(messages):
                    yield f"data: {response}\n\n"
            except Exception as e:
                yield f"data: Error in chat completion: {str(e)}\n\n"

        return StreamingHttpResponse(stream_chat(), content_type="text/event-stream")


class GenerateCompletionView(BaseGenerateCompletionView):
    permission_classes = [IsAuthenticated]


class APIKeyAuthenticatedGenerateCompletionView(BaseGenerateCompletionView):
    permission_classes = [APIKeyPermission]


class ProviderAPIKeyListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(cache_page(60))  # Cache for 1 minute
    def get(self, request):
        """List all provider API keys for the authenticated user"""
        cache_key = f"provider_keys_{request.user.id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        providers = ProviderAPIKey.objects.filter(user=request.user).select_related(
            "user"
        )
        serializer = ProviderAPIKeySerializer(providers, many=True)
        cache.set(cache_key, serializer.data, timeout=60)
        return Response(serializer.data)

    @transaction.atomic
    def post(self, request):
        """Create a new provider API key"""
        serializer = ProviderAPIKeyDetailsSerializer(data=request.data)
        if serializer.is_valid():
            # Check if user already has a key for this provider
            if ProviderAPIKey.objects.filter(
                user=request.user, provider=serializer.validated_data["provider"]
            ).exists():
                return Response(
                    {"error": "You already have an API key for this provider"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer.save(user=request.user)
            # Invalidate cache
            cache.delete(f"provider_keys_{request.user.id}")
            return Response(
                ProviderAPIKeySerializer(serializer.instance).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProviderAPIKeyDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return ProviderAPIKey.objects.select_related("user").get(pk=pk, user=user)
        except ProviderAPIKey.DoesNotExist:
            return None

    def get(self, request, pk):
        """Retrieve a specific provider API key"""
        cache_key = f"provider_key_{pk}_{request.user.id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        provider = self.get_object(pk, request.user)
        if not provider:
            return Response(
                {"error": "Provider API Key not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ProviderAPIKeyDetailsSerializer(provider)
        cache.set(cache_key, serializer.data, timeout=60)
        return Response(serializer.data)

    @transaction.atomic
    def put(self, request, pk):
        """Update a provider API key"""
        provider = self.get_object(pk, request.user)
        if not provider:
            return Response(
                {"error": "Provider API Key not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ProviderAPIKeyUpdateSerializer(
            provider, data=request.data, partial=False
        )
        if serializer.is_valid():
            serializer.save()
            # Invalidate caches
            cache.delete_many(
                [
                    f"provider_keys_{request.user.id}",
                    f"provider_key_{pk}_{request.user.id}",
                ]
            )
            return Response(ProviderAPIKeySerializer(provider).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    def delete(self, request, pk):
        """Delete a provider API key"""
        provider = self.get_object(pk, request.user)
        if not provider:
            return Response(
                {"error": "Provider API Key not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        provider.delete()
        # Invalidate caches
        cache.delete_many(
            [f"provider_keys_{request.user.id}", f"provider_key_{pk}_{request.user.id}"]
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class AIModelListView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(
        cache_page(3600)
    )  # Cache for 1 hour since model list rarely changes
    def get(self, request):
        """
        List all available AI models with optional filtering by name and provider.

        Query Parameters:
        - name: Filter models by name (case-insensitive partial match)
        - provider: Filter models by provider (case-insensitive exact match)
        """
        # Get query parameters
        name_filter = request.query_params.get("name", "").lower()
        provider_filter = request.query_params.get("provider", "").lower()

        # Generate cache key based on filters
        cache_key = f"ai_models_list_{name_filter}_{provider_filter}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        # Filter models based on query parameters
        filtered_models = AI_MODELS

        if name_filter:
            filtered_models = [
                model
                for model in filtered_models
                if name_filter in model["model_name"].lower()
            ]

        if provider_filter:
            filtered_models = [
                model
                for model in filtered_models
                if provider_filter == model["provider"].value.lower()
            ]

        # Transform the data to include additional useful information
        filtered_models = [
            {
                **model,
                "provider": model["provider"].value,
            }  # Convert enum to string value
            for model in filtered_models
        ]

        response_data = {
            "count": len(filtered_models),
            "models": filtered_models,
            "available_providers": sorted(
                list({model["provider"].value for model in AI_MODELS})
            ),
        }

        # Cache the filtered results
        cache.set(cache_key, response_data, timeout=3600)

        return Response(response_data)
