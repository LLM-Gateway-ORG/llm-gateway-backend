from django.urls import path
from .views import GenerateCompletionView, APIKeyAuthenticatedGenerateCompletionView

urlpatterns = [
    path('playground/prompt/', GenerateCompletionView.as_view(), name='generate_completion'),
    path('chat/completion/', APIKeyAuthenticatedGenerateCompletionView.as_view(), name='api_key_generate_completion'),
]
