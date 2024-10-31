from rest_framework.permissions import BasePermission
from .models import APIKey


class APIKeyPermission(BasePermission):
    """
    Custom permission to validate the API key provided in the headers.
    """

    def has_permission(self, request, view):
        # Retrieve the API key from headers (e.g., `X-API-KEY`)
        api_key = request.headers.get("X-API-KEY")

        if not api_key:
            return False  # API key not provided

        # Check if the API key exists and is valid
        try:
            api_key_obj = APIKey.objects.get(key=api_key)
            # Optionally, you could add more checks, like expiration or rate limits
            request.user = api_key_obj.user  # Set the user in the request
            return True
        except APIKey.DoesNotExist:
            return False  # Invalid API key
