from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReviewViewSet, ReviewCriterionViewSet, MarkViewSet, ApprovalViewSet

router = DefaultRouter()
router.register(r"reviews", ReviewViewSet, basename="reviews")
router.register(r"criteria", ReviewCriterionViewSet, basename="criteria")
router.register(r"marks", MarkViewSet, basename="marks")
router.register(r"approvals", ApprovalViewSet, basename="approvals")
urlpatterns = [path("", include(router.urls))]
