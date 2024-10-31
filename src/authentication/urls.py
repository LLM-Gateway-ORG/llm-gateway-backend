from django.urls import path
from .views import (
    UserRegistrationView,
    UserLoginView,
    UserProfileView,
    AuthTokenRefreshView,
    UserAPIView,
    APIKeyCreateView,
    APIKeyRetrieveDeleteView,
)

urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="register"),
    path("login/", UserLoginView.as_view(), name="login"),
    path("profile/", UserProfileView.as_view(), name="user-profile"),
    path("token/refresh/", AuthTokenRefreshView.as_view(), name="token_refresh"),
    path("users/", UserAPIView.as_view(), name="search-users"),
    path("apikey/", APIKeyCreateView.as_view(), name="apikey_create"),
    path(
        "apikey/<uuid:key_id>/",
        APIKeyRetrieveDeleteView.as_view(),
        name="apikey_detail",
    ),
]
