from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReportViewSet, dashboard_hod, dashboard_student, dashboard_faculty
router=DefaultRouter()
router.register(r'reports', ReportViewSet)
urlpatterns=[path('', include(router.urls)), path('dashboard/hod/', dashboard_hod), path('dashboard/student/', dashboard_student), path('dashboard/faculty/', dashboard_faculty)]
