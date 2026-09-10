from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProjectGroupViewSet,
    GroupMemberViewSet,
    GuideAssignmentViewSet,
    ReviewerAssignmentViewSet,
)

router = DefaultRouter()
router.register(r"groups", ProjectGroupViewSet, basename="groups")
router.register(r"group-members", GroupMemberViewSet)
router.register(r"guide-assignments", GuideAssignmentViewSet)
router.register(r"reviewer-assignments", ReviewerAssignmentViewSet)
urlpatterns = [path("", include(router.urls))]
