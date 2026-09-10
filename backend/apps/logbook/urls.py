from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FinalLogBookViewSet,
    hod_final_approval,
    generate_logbook,
    logbook_status,
    logbook_health,
)

router = DefaultRouter()
router.register(r"logbooks", FinalLogBookViewSet, basename="logbooks")
urlpatterns = [
    path("", include(router.urls)),
    path("groups/<int:group_id>/hod-final-approval/", hod_final_approval),
    path("groups/<int:group_id>/logbook/generate/", generate_logbook),
    path("groups/<int:group_id>/logbook/status/", logbook_status),
    path("logbook/health/", logbook_health),
]
