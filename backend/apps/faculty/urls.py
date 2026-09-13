from django.urls import path
from . import views

urlpatterns = [
    path("faculty/dashboard/", views.faculty_dashboard, name="faculty-dashboard"),
    path("reviewer/dashboard/", views.reviewer_dashboard, name="reviewer-dashboard"),
    path("faculty/groups/", views.faculty_groups, name="faculty-groups"),
    path("reviewer/groups/", views.reviewer_groups, name="reviewer-groups"),
    path(
        "faculty/groups/<int:pk>/",
        lambda r, pk: views.group_detail(r, pk, role_hint="faculty"),
        name="faculty-group-detail",
    ),
    path(
        "reviewer/groups/<int:pk>/",
        lambda r, pk: views.group_detail(r, pk, role_hint="reviewer"),
        name="reviewer-group-detail",
    ),
    path(
        "faculty/logbook/",
        lambda r: views.logbook_list(r, role_hint="faculty"),
        name="faculty-logbook",
    ),
    path(
        "reviewer/logbook/",
        lambda r: views.logbook_list(r, role_hint="reviewer"),
        name="reviewer-logbook",
    ),
    path(
        "faculty/logbook/<int:pk>/",
        lambda r, pk: views.logbook_review(r, pk, role_hint="faculty"),
        name="faculty-logbook-review",
    ),
    path(
        "reviewer/logbook/<int:pk>/",
        lambda r, pk: views.logbook_review(r, pk, role_hint="reviewer"),
        name="reviewer-logbook-review",
    ),
    path(
        "faculty/logbook/<int:pk>/review/",
        lambda r, pk: views.logbook_review(r, pk, role_hint="faculty"),
        name="faculty-logbook-review-post",
    ),
    path(
        "reviewer/logbook/<int:pk>/review/",
        lambda r, pk: views.logbook_review(r, pk, role_hint="reviewer"),
        name="reviewer-logbook-review-post",
    ),
    path(
        "faculty/submissions/",
        lambda r: views.submissions_list(r, role_hint="faculty"),
        name="faculty-submissions",
    ),
    path(
        "reviewer/submissions/",
        lambda r: views.submissions_list(r, role_hint="reviewer"),
        name="reviewer-submissions",
    ),
    path(
        "faculty/documents/",
        lambda r: views.documents_list(r, role_hint="faculty"),
        name="faculty-documents",
    ),
    path(
        "reviewer/documents/",
        lambda r: views.documents_list(r, role_hint="reviewer"),
        name="reviewer-documents",
    ),
    path(
        "faculty/documents/<int:pk>/review/",
        lambda r, pk: views.document_review(r, pk, role_hint="faculty"),
        name="faculty-document-review",
    ),
    path(
        "reviewer/documents/<int:pk>/review/",
        lambda r, pk: views.document_review(r, pk, role_hint="reviewer"),
        name="reviewer-document-review",
    ),
    path(
        "faculty/evaluations/",
        lambda r: views.evaluations(r, role_hint="faculty"),
        name="faculty-evaluations",
    ),
    path(
        "reviewer/evaluations/",
        lambda r: views.evaluations(r, role_hint="reviewer"),
        name="reviewer-evaluations",
    ),
    path(
        "faculty/evaluations/<int:pk>/finalize/",
        lambda r, pk: views.finalize_evaluation(r, pk, role_hint="faculty"),
        name="faculty-evaluation-finalize",
    ),
    path(
        "reviewer/evaluations/<int:pk>/finalize/",
        lambda r, pk: views.finalize_evaluation(r, pk, role_hint="reviewer"),
        name="reviewer-evaluation-finalize",
    ),
    path(
        "faculty/history/",
        lambda r: views.history(r, role_hint="faculty"),
        name="faculty-history",
    ),
    path(
        "reviewer/history/",
        lambda r: views.history(r, role_hint="reviewer"),
        name="reviewer-history",
    ),
    path(
        "faculty/notifications/",
        lambda r: views.notifications(r, role_hint="faculty"),
        name="faculty-notifications",
    ),
    path(
        "reviewer/notifications/",
        lambda r: views.notifications(r, role_hint="reviewer"),
        name="reviewer-notifications",
    ),
    path(
        "faculty/notifications/<int:pk>/read/",
        lambda r, pk: views.notification_read(r, pk, role_hint="faculty"),
        name="faculty-notification-read",
    ),
    path(
        "reviewer/notifications/<int:pk>/read/",
        lambda r, pk: views.notification_read(r, pk, role_hint="reviewer"),
        name="reviewer-notification-read",
    ),
    path(
        "faculty/notifications/mark_all_read/",
        lambda r: views.notifications_mark_all(r, role_hint="faculty"),
        name="faculty-notifications-mark-all",
    ),
    path(
        "reviewer/notifications/mark_all_read/",
        lambda r: views.notifications_mark_all(r, role_hint="reviewer"),
        name="reviewer-notifications-mark-all",
    ),
    path(
        "faculty/audit/",
        lambda r: views.audit_trail(r, role_hint="faculty"),
        name="faculty-audit",
    ),
    path(
        "reviewer/audit/",
        lambda r: views.audit_trail(r, role_hint="reviewer"),
        name="reviewer-audit",
    ),
    path(
        "faculty/progress/",
        lambda r: views.progress(r, role_hint="faculty"),
        name="faculty-progress",
    ),
    path(
        "reviewer/progress/",
        lambda r: views.progress(r, role_hint="reviewer"),
        name="reviewer-progress",
    ),
    path(
        "faculty/deadlines/",
        lambda r: views.deadlines(r, role_hint="faculty"),
        name="faculty-deadlines",
    ),
    path(
        "reviewer/deadlines/",
        lambda r: views.deadlines(r, role_hint="reviewer"),
        name="reviewer-deadlines",
    ),
]
