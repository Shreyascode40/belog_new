from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuditLogViewSet, DeadlineViewSet
router=DefaultRouter()
router.register(r'audit', AuditLogViewSet)
router.register(r'deadlines', DeadlineViewSet)
urlpatterns=[path('', include(router.urls))]
