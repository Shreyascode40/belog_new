from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/token/refresh/", TokenRefreshView.as_view()),
    path("api/v1/", include("apps.realtime.urls")),
    path("api/v1/", include("apps.faculty.urls")),
    path("api/v1/", include("apps.student.urls")),
    path("api/v1/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.academics.urls")),
    path("api/v1/", include("apps.groups.urls")),
    path("api/v1/", include("apps.projects.urls")),
    path("api/v1/", include("apps.submissions.urls")),
    path("api/v1/", include("apps.documents.urls")),
    path("api/v1/", include("apps.reviews.urls")),
    path("api/v1/", include("apps.co_po.urls")),
    path("api/v1/", include("apps.notifications.urls")),
    path("api/v1/", include("apps.audit.urls")),
    path("api/v1/", include("apps.reports.urls")),
    path("api/v1/", include("apps.logbook.urls")),
    path("api/v1/", include("apps.assessments.urls")),
    path("api/v1/", include("apps.workflow.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
