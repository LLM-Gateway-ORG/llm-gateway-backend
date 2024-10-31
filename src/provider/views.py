import json

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.http import StreamingHttpResponse, JsonResponse

from authentication.permissions import APIKeyPermission
from provider.models import ProviderAPIKey
from provider.utils import chat_completion
from provider.constants import AI_MODELS

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
