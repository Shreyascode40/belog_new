from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone
from .models import Submission, SubmissionVersion
from .serializers import SubmissionSerializer, SubmissionVersionSerializer


def check_access_grant(user, submission_or_group, stage):
    if user.role != "student":
        return
    group = (
        submission_or_group.group
        if hasattr(submission_or_group, "group")
        else submission_or_group
    )
    if stage.order >= 1:
        from apps.workflow.models import AccessGrant

        ag = AccessGrant.objects.filter(group=group, stage__order=1).first()
        if not ag or not ag.granted:
            raise PermissionDenied(
                {
                    "message": "Access not granted — guide must grant Level 1",
                    "errors": {
                        "access": [
                            "Level 1 locked — complete Information and wait for guide grant"
                        ]
                    },
                }
            )
    if stage.order > 0:
        from apps.projects.models import ProjectStage

        prev = ProjectStage.objects.filter(
            academic_year=stage.academic_year, order=stage.order - 1
        ).first()
        if prev:
            from apps.submissions.models import Submission

            sub = (
                Submission.objects.filter(group=group, section__stage=prev)
                .order_by("-created_at")
                .first()
            )
            if not sub or sub.status not in ["approved", "locked"]:
                raise PermissionDenied(
                    {
                        "message": f"Previous level {prev.name} not complete",
                        "errors": {
                            "level": [
                                f"Complete {prev.name} — current status {sub.status if sub else 'NOT_STARTED'}"
                            ]
                        },
                    }
                )


class SubmissionViewSet(viewsets.ModelViewSet):
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer

    def perform_create(self, serializer):
        obj = serializer.save()
        if obj.section and obj.section.stage.order >= 1:
            check_access_grant(self.request.user, obj, obj.section.stage)

    def perform_update(self, serializer):
        obj = serializer.save()
        if obj.section and obj.section.stage.order >= 1:
            check_access_grant(self.request.user, obj, obj.section.stage)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        s = self.get_object()
        s.status = "submitted"
        s.submitted_at = timezone.now()
        s.save()
        from apps.notifications.models import Notification

        # notify assigned guide/reviewer and HOD
        notified = False
        for ga in s.group.guide_assignments.filter(is_active=True):
            Notification.objects.create(
                recipient=ga.faculty,
                notification_type="submission",
                title="New Submission for Review",
                message=f"Group {s.group.group_number} Level {s.section.stage.order} — {s.section.stage.name} submitted by {request.user.email}",
                related_type="submission",
                related_id=s.id,
            )
            notified = True
        for ra in s.group.reviewer_assignments.filter(is_active=True):
            Notification.objects.create(
                recipient=ra.faculty,
                notification_type="submission",
                title="New Submission for Review",
                message=f"Group {s.group.group_number} Level {s.section.stage.order} — {s.section.stage.name} submitted",
                related_type="submission",
                related_id=s.id,
            )
            notified = True
        if not notified:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            for hod in User.objects.filter(role__in=["hod", "admin"]):
                Notification.objects.create(
                    recipient=hod,
                    notification_type="submission",
                    title="Submission (no guide)",
                    message=f"Group {s.group.group_number} submitted Level {s.section.stage.order} — no guide assigned",
                    related_type="submission",
                    related_id=s.id,
                )
        return Response(SubmissionSerializer(s).data)

    def _check_approver(self, submission):
        u = self.request.user
        if u.role in ["hod", "admin"]:
            return True
        if (
            submission.group.guide_assignments.filter(faculty=u).exists()
            or submission.group.reviewer_assignments.filter(faculty=u).exists()
        ):
            return True
        raise PermissionDenied(
            {
                "message": "Only assigned Guide/Reviewer or HOD can approve",
                "errors": {"permission": ["Not assigned to this group"]},
            }
        )

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        s = self.get_object()
        self._check_approver(s)
        s.status = "approved"
        s.reviewed_at = timezone.now()
        s.reviewed_by = request.user
        s.save()
        from apps.notifications.models import Notification
        from apps.audit.models import AuditLog

        for member in s.group.members.filter(status="accepted"):
            Notification.objects.create(
                recipient=member.student,
                notification_type="approval",
                title="Submission Approved",
                message=f"Level {s.section.stage.order} — {s.section.stage.name} approved by {request.user.email}",
                related_type="submission",
                related_id=s.id,
            )
        # also notify HOD
        from django.contrib.auth import get_user_model

        User = get_user_model()
        for hod in User.objects.filter(role__in=["hod", "admin"]):
            Notification.objects.create(
                recipient=hod,
                notification_type="approval",
                title="Submission Approved",
                message=f"Group {s.group.group_number} Level {s.section.stage.order} approved by {request.user.email}",
                related_type="submission",
                related_id=s.id,
            )
        AuditLog.objects.create(
            actor=request.user,
            actor_role=request.user.role,
            action="submission_approved",
            entity_type="submission",
            entity_id=s.id,
            new_value={
                "group": s.group.id,
                "stage": s.section.stage.id,
                "status": "approved",
            },
        )
        return Response(SubmissionSerializer(s).data)

    @action(detail=True, methods=["post"])
    def request_changes(self, request, pk=None):
        s = self.get_object()
        self._check_approver(s)
        s.status = "changes_required"
        s.review_remarks = request.data.get("remarks", "") or request.data.get(
            "review_remarks", ""
        )
        s.save()
        from apps.notifications.models import Notification
        from apps.audit.models import AuditLog

        for member in s.group.members.filter(status="accepted"):
            Notification.objects.create(
                recipient=member.student,
                notification_type="change_request",
                title="Changes Requested",
                message=f"Level {s.section.stage.order} — {s.section.stage.name}: {s.review_remarks}",
                related_type="submission",
                related_id=s.id,
            )
        AuditLog.objects.create(
            actor=request.user,
            actor_role=request.user.role,
            action="changes_requested",
            entity_type="submission",
            entity_id=s.id,
            new_value={"group": s.group.id, "remark": s.review_remarks},
        )
        return Response(SubmissionSerializer(s).data)

    @action(detail=True, methods=["post"])
    def resubmit(self, request, pk=None):
        s = self.get_object()
        s.status = "resubmitted"
        s.save()
        SubmissionVersion.objects.create(
            submission=s,
            version_number=s.version,
            content=s.content,
            submitted_by=request.user,
        )
        s.version += 1
        s.save()
        return Response(SubmissionSerializer(s).data)

    @action(detail=True, methods=["post"])
    def lock(self, request, pk=None):
        s = self.get_object()
        s.status = "locked"
        s.save()
        return Response(SubmissionSerializer(s).data)


class SubmissionVersionViewSet(viewsets.ModelViewSet):
    queryset = SubmissionVersion.objects.all()
    serializer_class = SubmissionVersionSerializer
