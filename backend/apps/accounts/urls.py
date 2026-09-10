
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import register, login_view, me, UserViewSet, StudentProfileViewSet, FacultyProfileViewSet
router=DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'students', StudentProfileViewSet, basename='students')
router.register(r'faculty', FacultyProfileViewSet, basename='faculty')
urlpatterns=[path('auth/register/', register), path('auth/login/', login_view), path('auth/me/', me), path('', include(router.urls))]
