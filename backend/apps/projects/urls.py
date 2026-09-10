from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProjectViewSet,
    ProjectStageViewSet,
    StageDependencyViewSet,
    SectionViewSet,
    ActivityViewSet,
)

router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="projects")
router.register(r"stages", ProjectStageViewSet)
router.register(r"stage-dependencies", StageDependencyViewSet)
router.register(r"sections", SectionViewSet)
router.register(r"activities", ActivityViewSet)
urlpatterns = [path("", include(router.urls))]
