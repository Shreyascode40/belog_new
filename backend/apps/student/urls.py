from django.urls import path
from . import views

urlpatterns = [
    path("student/dashboard/", views.dashboard, name="student-dashboard"),
    path("student/profile/", views.profile_view, name="student-profile"),
    path("student/group/", views.group_view, name="student-group"),
    path("student/logbook/", views.logbook_list_create, name="student-logbook-list"),
    path(
        "student/logbook/<int:pk>/", views.logbook_detail, name="student-logbook-detail"
    ),
    path(
        "student/logbook/<int:pk>/submit/",
        views.logbook_submit,
        name="student-logbook-submit",
    ),
    path("student/progress/", views.progress_view, name="student-progress"),
    path("student/documents/", views.documents_view, name="student-documents"),
    path(
        "student/documents/<int:pk>/versions/",
        views.document_versions,
        name="student-document-versions",
    ),
    path("student/reviews/", views.reviews_view, name="student-reviews"),
    path(
        "student/notifications/", views.notifications_view, name="student-notifications"
    ),
    path(
        "student/notifications/<int:pk>/read/",
        views.notification_read,
        name="student-notification-read",
    ),
    path(
        "student/notifications/mark_all_read/",
        views.notifications_mark_all,
        name="student-notifications-mark-all",
    ),
    path(
        "student/final-logbook/", views.final_logbook_view, name="student-final-logbook"
    ),
    path(
        "student/final-logbook/generate/",
        views.final_logbook_generate,
        name="student-final-logbook-generate",
    ),
    path("student/audit/", views.audit_view, name="student-audit"),
]
