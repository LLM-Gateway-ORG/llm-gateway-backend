from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AppsViewSet

router = DefaultRouter()
router.register(r"", AppsViewSet, basename="app")

urlpatterns = [
    path("", include(router.urls)),
]
