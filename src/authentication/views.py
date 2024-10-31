from rest_framework import generics, status, views, permissions
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from django.contrib.auth import authenticate
from rest_framework.pagination import LimitOffsetPagination
import secrets

from .models import AuthUser, APIKey
from .serializers import AuthUserSerializer, APIKeySerializer


# Create your views here.
class UserRegistrationView(generics.CreateAPIView):
    queryset = AuthUser.objects.all()
    serializer_class = AuthUserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": AuthUserSerializer(user).data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_201_CREATED,
        )


class UserLoginView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = AuthUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class AuthTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        response.data["custom_message"] = "Refresh successful"
        return response


class UserAPIView(generics.ListAPIView):
    serializer_class = AuthUserSerializer
    permission_classes = [
        permissions.IsAuthenticated
    ]
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        current_user = self.request.user
        queryset = AuthUser.objects.all().exclude(
            id=current_user.id
        )  # Exclude the current user
        keyword = self.request.query_params.get("q", None)
        if keyword:
            email_match = queryset.filter(email__iexact=keyword)
            if email_match.exists():
                return email_match
            name_match = queryset.filter(
                firstname__icontains=keyword
            ) | queryset.filter(lastname__icontains=keyword)
            return name_match
        return queryset
    
class APIKeyCreateView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Generate a new API key for the authenticated user
        api_key_value = secrets.token_urlsafe(32)
        api_key = APIKey.objects.create(key=api_key_value, user=request.user)
        serializer = APIKeySerializer(api_key)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class APIKeyRetrieveDeleteView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, key_id):
        # Retrieve a specific API key for the authenticated user
        try:
            api_key = APIKey.objects.get(id=key_id, user=request.user)
            serializer = APIKeySerializer(api_key)
            return Response(serializer.data)
        except APIKey.DoesNotExist:
            return Response({"error": "API key not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, key_id):
        # Delete a specific API key for the authenticated user
        try:
            api_key = APIKey.objects.get(id=key_id, user=request.user)
            api_key.delete()
            return Response({"message": "API key deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except APIKey.DoesNotExist:
            return Response({"error": "API key not found"}, status=status.HTTP_404_NOT_FOUND)