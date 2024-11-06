from rest_framework import generics, status, views, permissions
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from django.contrib.auth import authenticate
from rest_framework.pagination import LimitOffsetPagination
import secrets
import requests
from django.contrib.auth import authenticate
from google.auth.transport import requests as google_requests
from django.conf import settings
from django.db import transaction
from google.oauth2 import id_token
from urllib.parse import urlencode

from .models import AuthUser, APIKey
from .serializers import AuthUserSerializer, APIKeySerializer, ResetPasswordSerializer


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


class APIKeyRetrieveDeleteView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, key_id):
        # Retrieve a specific API key for the authenticated user
        try:
            api_key = APIKey.objects.get(id=key_id, user=request.user)
            serializer = APIKeySerializer(api_key)
            data = serializer.data
            # Add the actual API key value to the response
            data["key"] = api_key.key
            return Response(data)
        except APIKey.DoesNotExist:
            return Response(
                {"error": "API key not found"}, status=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request, key_id):
        # Delete a specific API key for the authenticated user
        try:
            api_key = APIKey.objects.get(id=key_id, user=request.user)
            api_key.delete()
            return Response(
                {"message": "API key deleted successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )
        except APIKey.DoesNotExist:
            return Response(
                {"error": "API key not found"}, status=status.HTTP_404_NOT_FOUND
            )


class APIKeyView(generics.ListCreateAPIView):
    serializer_class = APIKeySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        return APIKey.objects.filter(user=self.request.user).order_by('id')

    def post(self, request, *args, **kwargs):
        # Generate a new API key for the authenticated user
        api_key_value = secrets.token_urlsafe(32)
        api_key = APIKey.objects.create(key=api_key_value, user=request.user)
        serializer = APIKeySerializer(api_key)
        return Response(
            {**serializer.data, "key": api_key.key}, status=status.HTTP_201_CREATED
        )


class GoogleAuthBaseView(views.APIView):
    permission_classes = [AllowAny]

    def _get_or_create_user(self, email, user_data):
        """Create or update user from Google data"""
        try:
            user = AuthUser.objects.get(email=email)
            # Update existing user data if needed
            user.firstname = user_data.get("given_name", user.firstname)
            user.lastname = user_data.get("family_name", user.lastname)
            user.save()
        except AuthUser.DoesNotExist:
            # Create new user
            with transaction.atomic():
                user_details = {
                    "email": email,
                    "username": email,
                    "firstname": user_data.get("given_name", ""),
                    "lastname": user_data.get("family_name", ""),
                    "auth_provider": "google",
                    "password": secrets.token_urlsafe(32),
                }
                serializer = AuthUserSerializer(data=user_details)
                serializer.is_valid(raise_exception=True)
                user = serializer.save()
        return user

    def _generate_tokens(self, user):
        """Generate JWT tokens for user"""
        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }


class GoogleLoginURLView(GoogleAuthBaseView):
    def get(self, request):
        """Generate Google OAuth2 URL for client"""
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_OAUTH2_REDIRECT_URI,
            "response_type": "code",
            "scope": "email profile openid",
            "access_type": "offline",
            "prompt": "consent",
        }

        oauth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

        return Response({"oauth_url": oauth_url}, status=status.HTTP_200_OK)


class GoogleCallbackView(GoogleAuthBaseView):
    def post(self, request):
        """Handle Google OAuth callback"""
        code = request.GET.get("code")

        if not code:
            return Response(
                {"error": "Authorization code is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Exchange code for tokens
            token_response = self._get_google_tokens(code)

            # Verify ID token
            id_info = self._verify_google_token(token_response["id_token"])

            # Get or create user
            user = self._get_or_create_user(id_info["email"], id_info)

            # Generate JWT tokens
            jwt_tokens = self._generate_tokens(user)

            return Response(
                {
                    "user": AuthUserSerializer(user).data,
                    "google_tokens": {
                        "access_token": token_response.get("access_token"),
                        "refresh_token": token_response.get("refresh_token"),
                        "id_token": token_response.get("id_token"),
                        "expires_in": token_response.get("expires_in"),
                    },
                    "jwt_tokens": jwt_tokens,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def _get_google_tokens(self, code):
        """Exchange authorization code for tokens"""
        token_url = "https://oauth2.googleapis.com/token"

        data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_OAUTH2_REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        response = requests.post(token_url, data=data)

        if response.status_code != 200:
            raise Exception("Failed to get Google tokens")

        return response.json()

    def _verify_google_token(self, token):
        """Verify Google ID token"""
        try:
            return id_token.verify_oauth2_token(
                token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
            )
        except ValueError:
            raise Exception("Invalid Google token")


class GoogleTokenRefreshView(GoogleAuthBaseView):
    def post(self, request):
        """Refresh Google access token"""
        refresh_token = request.data.get("refresh_token")

        if not refresh_token:
            return Response(
                {"error": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token_url = "https://oauth2.googleapis.com/token"

            data = {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            }

            response = requests.post(token_url, data=data)

            if response.status_code != 200:
                raise Exception("Failed to refresh Google token")

            return Response(response.json(), status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(views.APIView):
    def post(self, request):
        user = request.user
        serializer = ResetPasswordSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        old_password = serializer.validated_data["old_password"]
        new_password = serializer.validated_data["new_password"]

        # Check if new password is same as old password
        if old_password == new_password:
            return Response(
                {"error": "New password must be different from old password"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify old password
        if not user.check_password(old_password):
            return Response(
                {"error": "Invalid old password"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Set new password
        user.set_password(new_password)
        user.save()

        # Generate new tokens since password changed
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Password changed successfully",
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_200_OK,
        )
