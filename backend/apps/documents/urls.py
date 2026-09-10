
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet, DocumentVersionViewSet
router=DefaultRouter()
router.register(r'documents', DocumentViewSet)
router.register(r'document-versions', DocumentVersionViewSet)
urlpatterns=[path('', include(router.urls))]
