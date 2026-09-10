from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.conf import settings
from .models import FinalLogBook, HODFinalApproval
from .serializers import FinalLogBookSerializer, HODFinalApprovalSerializer


class FinalLogBookViewSet(viewsets.ModelViewSet):
    serializer_class = FinalLogBookSerializer

    def get_queryset(self):
        qs = FinalLogBook.objects.all()
        u = self.request.user
        if u and u.role == "student":
            return qs.filter(group__members__student=u).distinct()
        if u and u.role in ["faculty", "reviewer"]:
            return (
                qs.filter(group__guide_assignments__faculty=u).distinct()
                | qs.filter(group__reviewer_assignments__faculty=u).distinct()
            )
        return qs

    @action(detail=True, methods=["post"])
    def generate(self, request, pk=None):
        o = self.get_object()
        o.status = "completed"
        o.generated_at = timezone.now()
        o.generated_by = request.user
        o.save()
        return Response(FinalLogBookSerializer(o).data)

    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        o = self.get_object()
        return Response({"success": True, "data": FinalLogBookSerializer(o).data})


def _check_conditions(group):
    errors = {}
    from apps.projects.models import ProjectStage
    from apps.submissions.models import Submission
    from apps.reviews.models import Review

    stages = ProjectStage.objects.filter(
        academic_year=group.academic_year, is_required=True
    )
    if not stages.exists():
        stages = ProjectStage.objects.filter(is_required=True)
    not_locked = []
    for s in stages:
        sub = (
            Submission.objects.filter(group=group, section__stage=s)
            .order_by("-created_at")
            .first()
        )
        if not sub or sub.status != "locked":
            not_locked.append(s.name)
    if not_locked:
        errors["stages"] = [f"{n} not yet LOCKED" for n in not_locked]
    reviews = Review.objects.filter(group=group)
    not_final = []
    for r in reviews:
        if r.status != "finalized":
            not_final.append(f"Review {r.review_number} not FINALIZED")
    if not reviews.exists():
        errors["reviews"] = ["No reviews configured"]
    elif not_final:
        errors["reviews"] = not_final
    try:
        hod = HODFinalApproval.objects.get(group=group)
        if not hod.approved:
            errors["hod_approval"] = ["Not yet granted"]
    except HODFinalApproval.DoesNotExist:
        errors["hod_approval"] = ["Not yet granted"]
    return errors


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def hod_final_approval(request, group_id):
    from apps.groups.models import ProjectGroup

    if request.user.role not in ["hod", "admin"]:
        return Response(
            {
                "success": False,
                "message": "HOD only",
                "errors": {"role": ["HOD role required"]},
            },
            status=403,
        )
    group = get_object_or_404(ProjectGroup, id=group_id)
    approved = request.data.get("approved", True)
    remark = request.data.get("remark", "")
    from apps.audit.models import AuditLog

    errors = _check_conditions(group)
    snapshot = {"checked_at": timezone.now().isoformat(), "conditions": errors}
    obj, created = HODFinalApproval.objects.update_or_create(
        group=group,
        defaults={
            "approved_by": request.user,
            "approved": bool(approved),
            "remark": remark,
            "approved_at": timezone.now() if approved else None,
            "checklist_snapshot": snapshot,
        },
    )
    AuditLog.objects.create(
        actor=request.user,
        actor_role=request.user.role,
        action="final_submission_approved",
        entity_type="hod_final_approval",
        entity_id=obj.id,
        new_value={"group": group.id, "approved": bool(approved)},
    )
    return Response({"success": True, "data": HODFinalApprovalSerializer(obj).data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_logbook(request, group_id):
    from apps.groups.models import ProjectGroup
    from apps.notifications.models import Notification
    from apps.logbook.services import PDFGenerationError

    group = get_object_or_404(ProjectGroup, id=group_id)
    errors = _check_conditions(group)
    if errors:
        return Response(
            {"success": False, "message": "Cannot generate logbook", "errors": errors},
            status=403,
        )
    from apps.logbook.services import generate_pdf

    last = FinalLogBook.objects.filter(group=group).order_by("-version").first()
    version = (last.version + 1) if last else 1
    lb = FinalLogBook.objects.create(
        group=group,
        academic_year=group.academic_year,
        status="generating",
        version=version,
        generated_by=request.user,
        generated_at=timezone.now(),
    )
    try:
        pdf_path = generate_pdf(group, lb)
        lb.pdf_path = pdf_path
        lb.status = "completed"
        lb.save()
        from apps.audit.models import AuditLog

        AuditLog.objects.create(
            actor=request.user,
            actor_role=request.user.role,
            action="logbook_generated",
            entity_type="final_logbook",
            entity_id=lb.id,
            new_value={"group": group.id, "version": version},
        )
        for member in group.members.all():
            Notification.objects.create(
                recipient=member.student,
                notification_type="system",
                title="Logbook generated",
                message=f"Group {group.group_number} logbook v{version} ready",
            )
    except PDFGenerationError as e:
        lb.status = "pending"
        lb.remarks = str(e)
        lb.save()
        from apps.audit.models import AuditLog

        AuditLog.objects.create(
            actor=request.user,
            actor_role=request.user.role,
            action="logbook_generated",
            entity_type="final_logbook",
            entity_id=lb.id,
            new_value={"error": str(e)},
        )
        return Response(
            {"success": False, "message": str(e), "errors": {"pdf": [str(e)]}},
            status=503,
        )
    except Exception as e:
        lb.status = "pending"
        lb.remarks = str(e)
        lb.save()
        return Response({"success": False, "message": str(e)}, status=500)
    return Response({"success": True, "data": FinalLogBookSerializer(lb).data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def logbook_status(request, group_id):
    from apps.groups.models import ProjectGroup

    group = get_object_or_404(ProjectGroup, id=group_id)
    errors = _check_conditions(group)
    can_generate = len(errors) == 0
    lb = FinalLogBook.objects.filter(group=group).order_by("-version").first()
    return Response(
        {
            "success": True,
            "data": {
                "can_generate": can_generate,
                "errors": errors,
                "latest": FinalLogBookSerializer(lb).data if lb else None,
            },
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def logbook_health(request):
    if request.user.role not in ["hod", "admin"]:
        return Response({"success": False, "message": "Admin only"}, status=403)
    from apps.logbook.services import health_check

    ok = health_check()
    if ok:
        return Response({"success": True, "data": {"pdf_renderer": "ok"}})
    return Response(
        {
            "success": False,
            "message": "PDF renderer unavailable",
            "errors": {
                "pdf": [
                    "Renderer health check failed — check server logs and system dependencies"
                ]
            },
        },
        status=503,
    )
