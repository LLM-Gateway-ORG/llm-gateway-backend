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
from litellm import model_cost

from authentication.permissions import APIKeyPermission
from provider.models import ProviderAPIKey
from provider.utils import chat_completion
from provider.serializers import (
    ProviderAPIKeySerializer,
    ProviderAPIKeyCreateSerializer,
    ProviderAPIKeyUpdateSerializer,
)
from provider.helpers import decrypt_value

# Create your views here.


class BaseGenerateCompletionView(APIView):
    def get_permission_classes(self):
        """Override this method in subclasses to set specific permissions."""
        raise NotImplementedError("Subclasses must define permission classes")

    def generate_stream_response(self, messages, model_name, provider_obj):
        """Generate streaming response for async endpoints"""

        async def stream_chat():
            try:
                llm = chat_completion(
                    api_key=decrypt_value(provider_obj.api_key),
                    provider=provider_obj.provider,
                )
                async for response in llm.async_completion(model_name, messages):
                    yield f"data: {response}\n\n"
            except Exception as e:
                yield f"data: Error in chat completion: {str(e)}\n\n"

        return StreamingHttpResponse(
            streaming_content=stream_chat(), content_type="text/event-stream"
        )

    def generate_sync_response(self, messages, model_name, provider_obj):
        """Generate complete response for non-streaming endpoints"""
        try:
            llm = chat_completion(
                api_key=decrypt_value(provider_obj.api_key),
                provider=provider_obj.provider,
            )

            full_response = llm.completion(model_name, messages)
            return JsonResponse({"response": full_response})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    def validate_request(self, request):
        """Common validation logic"""
        try:
            body = request.data
            messages = body.get("messages", [])
            model_name = body.get("model_name")
            provider_id = body.get("provider_id")

            provider_list = ProviderAPIKey.objects.filter(
                id=provider_id, user=request.user
            )
            if not provider_list.exists():
                return None, JsonResponse(
                    {"error": "Provider Not Found or Access Denied"}, status=400
                )

            provider_obj = provider_list.first()

            if not any(
                key == model_name and i["litellm_provider"] == provider_obj.provider
                for key, i in model_cost.items()
            ):
                return None, JsonResponse(
                    {"error": "Model Not Found for Provider"}, status=400
                )

            return (messages, model_name, provider_obj), None
        except json.JSONDecodeError:
            return None, JsonResponse({"error": "Invalid JSON body"}, status=400)


class PlaygroundGenerateCompletionView(BaseGenerateCompletionView):
    permission_classes = [IsAuthenticated]

    def post(self, request) -> StreamingHttpResponse:
        validation_result, error_response = self.validate_request(request)
        if error_response:
            return error_response

        messages, model_name, provider_obj = validation_result
        return self.generate_stream_response(messages, model_name, provider_obj)


class APIKeyAuthenticatedGenerateCompletionView(BaseGenerateCompletionView):
    permission_classes = [APIKeyPermission]

    def post(self, request):
        validation_result, error_response = self.validate_request(request)
        if error_response:
            return error_response

        messages, model_name, provider_obj = validation_result
        return self.generate_sync_response(messages, model_name, provider_obj)


class ProviderAPIKeyListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(
        cache_page(3600)
    )  # Cache for 1 hour since model list rarely changes
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
        cache.set(cache_key, serializer.data, timeout=3600)
        return Response(serializer.data)

    @transaction.atomic
    def post(self, request):
        """Create a new provider API key"""
        serializer = ProviderAPIKeyCreateSerializer(data=request.data)
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
        """Retrieve a specific provider API key with decrypted api key"""
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
        serializer = ProviderAPIKeySerializer(provider)
        cache.set(
            cache_key,
            {**serializer.data, "api_key": provider.get_decrypted_api_key()},
            timeout=60,
        )
        return Response(
            {**serializer.data, "api_key": provider.get_decrypted_api_key()}
        )

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
    @method_decorator(
        cache_page(3600)
    )  # Cache for 1 hour since model list rarely changes
    def get(self, request):
        """
        List all available AI models with optional filtering by name and provider.

        Query Parameters:
        - name: Filter models by name (case-insensitive partial match)
        - provider: Filter models by provider (case-insensitive exact match)
        - limit: Number of results to return (default: all)
        - offset: Number of results to skip (default: 0)
        """
        # Get query parameters
        name_filter = request.query_params.get("name", "").lower()
        provider_filter = request.query_params.get("provider", "").lower()
        limit = request.query_params.get("limit")
        offset = int(request.query_params.get("offset", 0))

        # Generate cache key based on filters
        cache_key = f"ai_models_list_{name_filter}_{provider_filter}_{limit}_{offset}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        # Filter models based on query parameters
        filtered_models = []
        for name, model in model_cost.items():
            if name != "sample_spec":
                filtered_models.append(
                    {**model, "provider": model["litellm_provider"], "model_name": name}
                )

        if name_filter:
            filtered_models = [
                model for model in filtered_models if name_filter in model["model_name"]
            ]

        if provider_filter:
            filtered_models = [
                model
                for model in filtered_models
                if provider_filter == model["provider"]
            ]

        # Apply pagination
        total_count = len(filtered_models)
        if limit:
            limit = int(limit)
            filtered_models = filtered_models[offset : offset + limit]

        response_data = {
            "count": total_count,
            "models": filtered_models,
            "available_providers": sorted(
                list(
                    {
                        model["litellm_provider"]
                        for model in list(model_cost.values())[1:]
                    }
                )
            ),
            "offset": offset,
            "limit": limit if limit else None,
        }

        # Cache the filtered results
        cache.set(cache_key, response_data, timeout=3600)

        return Response(response_data)
