from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SubmissionViewSet, SubmissionVersionViewSet

router = DefaultRouter()
router.register(r"submissions", SubmissionViewSet, basename="submissions")
router.register(
    r"submission-versions", SubmissionVersionViewSet, basename="submission-versions"
)
urlpatterns = [path("", include(router.urls))]
