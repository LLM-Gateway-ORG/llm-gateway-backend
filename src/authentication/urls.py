from django.urls import path
from .views import (
    UserRegistrationView,
    UserLoginView,
    UserProfileView,
    AuthTokenRefreshView,
    APIKeyCreateView,
    APIKeyRetrieveDeleteView,
    GoogleLoginURLView,
    GoogleCallbackView,
    GoogleTokenRefreshView,
    ResetPasswordView,
)

urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="register"),
    path("login/", UserLoginView.as_view(), name="login"),
    path("profile/", UserProfileView.as_view(), name="user-profile"),
    path("password/reset/", ResetPasswordView.as_view(), name="reset-password"),
    path("token/refresh/", AuthTokenRefreshView.as_view(), name="token_refresh"),
    path("google/login/", GoogleLoginURLView.as_view(), name="google-login-url"),
    path(
        "google/login/callback/", GoogleCallbackView.as_view(), name="google-callback"
    ),
    path(
        "google/login/refresh/", GoogleTokenRefreshView.as_view(), name="google-refresh"
    ),
    path("apikey/", APIKeyCreateView.as_view(), name="apikey_create"),
    path(
        "apikey/<uuid:key_id>/",
        APIKeyRetrieveDeleteView.as_view(),
        name="apikey_detail",
    ),
]
