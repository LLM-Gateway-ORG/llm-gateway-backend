from django.urls import path
from .views import (
    PlaygroundGenerateCompletionView,
    APIKeyAuthenticatedGenerateCompletionView,
    ProviderAPIKeyListCreateView,
    ProviderAPIKeyDetailView,
    AIModelListView,
)

app_name = "provider"

urlpatterns = [
    # AI Completion endpoints
    path(
        "playground/generate/completion/",
        PlaygroundGenerateCompletionView.as_view(),
        name="generate-completion",
    ),
    path(
        "generate/completion/",
        APIKeyAuthenticatedGenerateCompletionView.as_view(),
        name="api-generate-completion",
    ),
    # Provider API Key CRUD endpoints
    path("", ProviderAPIKeyListCreateView.as_view(), name="provider-list"),
    path("<uuid:pk>/", ProviderAPIKeyDetailView.as_view(), name="provider-detail"),
    # AI Models listing endpoint
    path("ai/models/", AIModelListView.as_view(), name="ai-model-list"),
]
