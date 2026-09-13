from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet, DocumentVersionViewSet

router = DefaultRouter()
router.register(r"documents", DocumentViewSet, basename="documents")
router.register(
    r"document-versions", DocumentVersionViewSet, basename="document-versions"
)
urlpatterns = [path("", include(router.urls))]
