from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from .models import Project, ProjectStage, StageDependency, Section, Activity
from .serializers import (
    ProjectSerializer,
    ProjectStageSerializer,
    StageDependencySerializer,
    SectionSerializer,
    ActivitySerializer,
)


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        qs = Project.objects.all()
        u = self.request.user
        if u and u.is_authenticated and u.role == "student":
            return qs.filter(group__members__student=u).distinct()
        if u and u.role in ["faculty", "reviewer"]:
            return (
                qs.filter(group__guide_assignments__faculty=u).distinct()
                | qs.filter(group__reviewer_assignments__faculty=u).distinct()
            )
        return qs


class ProjectStageViewSet(viewsets.ModelViewSet):
    queryset = ProjectStage.objects.all().order_by("order")
    serializer_class = ProjectStageSerializer


class StageDependencyViewSet(viewsets.ModelViewSet):
    queryset = StageDependency.objects.all()
    serializer_class = StageDependencySerializer


class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer

    def _check_previous_level(self, obj):
        if self.request.user.role != "student":
            return
        # Level 1 gate
        if obj.stage.order >= 1:
            from apps.workflow.models import AccessGrant

            ag = AccessGrant.objects.filter(group=obj.group, stage__order=1).first()
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
        # Generic previous-level complete check
        if obj.stage.order > 0:
            from apps.submissions.models import Submission

            prev = obj.stage.__class__.objects.filter(
                academic_year=obj.stage.academic_year, order=obj.stage.order - 1
            ).first()
            if prev:
                sub = (
                    Submission.objects.filter(group=obj.group, section__stage=prev)
                    .order_by("-created_at")
                    .first()
                )
                if not sub or sub.status not in ["approved", "locked"]:
                    raise PermissionDenied(
                        {
                            "message": f"Previous level {prev.name} not complete",
                            "errors": {
                                "level": [
                                    f"Complete {prev.name} ({prev.order}) — current status {sub.status if sub else 'NOT_STARTED'}"
                                ]
                            },
                        }
                    )

    def perform_create(self, serializer):
        obj = serializer.save()
        try:
            self._check_previous_level(obj)
        except PermissionDenied:
            obj.delete()
            raise

    def perform_update(self, serializer):
        obj = serializer.save()
        self._check_previous_level(obj)


class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
