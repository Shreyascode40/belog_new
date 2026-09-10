from django.urls import path
from .views import stage_status, group_level, access_grant, guide_queue

urlpatterns = [
    path("workflow/status/<int:group_id>/", stage_status),
    path("groups/<int:group_id>/level/", group_level),
    path("groups/<int:group_id>/stages/<int:stage_id>/access-grant/", access_grant),
    path("guide/queue/", guide_queue),
]
