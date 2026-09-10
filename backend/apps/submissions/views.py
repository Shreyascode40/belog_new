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
        return Response(SubmissionSerializer(s).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        s = self.get_object()
        s.status = "approved"
        s.reviewed_at = timezone.now()
        s.reviewed_by = request.user
        s.save()
        return Response(SubmissionSerializer(s).data)

    @action(detail=True, methods=["post"])
    def request_changes(self, request, pk=None):
        s = self.get_object()
        s.status = "changes_required"
        s.review_remarks = request.data.get("remarks", "")
        s.save()
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
