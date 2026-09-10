from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import COViewSet, POViewSet, COPOMappingViewSet, COAttainmentViewSet, POAttainmentViewSet, calculate_attainment
router=DefaultRouter()
router.register(r'cos', COViewSet)
router.register(r'pos', POViewSet)
router.register(r'mappings', COPOMappingViewSet)
router.register(r'co-attainments', COAttainmentViewSet)
router.register(r'po-attainments', POAttainmentViewSet)
urlpatterns=[path('', include(router.urls)), path('calculate/', calculate_attainment)]
