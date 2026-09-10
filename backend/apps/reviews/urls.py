
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReviewViewSet, ReviewCriterionViewSet, MarkViewSet, ApprovalViewSet
router=DefaultRouter()
router.register(r'reviews', ReviewViewSet)
router.register(r'criteria', ReviewCriterionViewSet)
router.register(r'marks', MarkViewSet)
router.register(r'approvals', ApprovalViewSet)
urlpatterns=[path('', include(router.urls))]
