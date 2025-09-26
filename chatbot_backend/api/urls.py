from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import health, ChatSessionViewSet, MessageViewSet

router = DefaultRouter()
router.register(r"sessions", ChatSessionViewSet, basename="session")
router.register(r"messages", MessageViewSet, basename="message")

urlpatterns = [
    path("health/", health, name="Health"),
    path("", include(router.urls)),
]
