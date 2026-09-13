from django.urls import path
from . import views

urlpatterns = [
    path("realtime/updates/", views.updates, name="realtime-updates"),
    path("realtime/stream/", views.stream, name="realtime-stream"),
]
