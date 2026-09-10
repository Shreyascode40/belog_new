
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DepartmentViewSet, AcademicYearViewSet, SemesterViewSet
router=DefaultRouter()
router.register(r'departments', DepartmentViewSet)
router.register(r'academic-years', AcademicYearViewSet)
router.register(r'semesters', SemesterViewSet)
urlpatterns=[path('', include(router.urls))]
