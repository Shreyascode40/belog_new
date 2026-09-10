from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.projects.models import ProjectStage, Section
from apps.submissions.models import Submission
from apps.workflow.models import AccessGrant
from django.shortcuts import get_object_or_404
from apps.groups.models import ProjectGroup


def compute_level(group):
    stages = ProjectStage.objects.filter(academic_year=group.academic_year).order_by(
        "order"
    )
    if not stages.exists():
        stages = ProjectStage.objects.all().order_by("order")
    current_stage = None
    current_status = "NOT_STARTED"
    for s in stages:
        sub = (
            Submission.objects.filter(group=group, section__stage=s)
            .order_by("-created_at")
            .first()
        )
        sec = Section.objects.filter(group=group, stage=s).first()
        st = "NOT_STARTED"
        if sub:
            st = sub.status.upper()
        elif sec:
            st = sec.status.upper()
        if st in ["APPROVED", "LOCKED"]:
            continue
        else:
            current_stage = s
            current_status = st
            break
    if current_stage is None and stages.exists():
        current_stage = stages.last()
        current_status = "LOCKED"
    is_granted = True
    if current_stage and current_stage.order == 1:
        ag = AccessGrant.objects.filter(group=group, stage=current_stage).first()
        is_granted = ag.granted if ag else False
    elif current_stage and current_stage.order == 0:
        is_granted = True
    labels = {
        "NOT_STARTED": f"Start {current_stage.name}" if current_stage else "Start",
        "DRAFT": "Continue Editing",
        "SUBMITTED": "Waiting for guide approval",
        "UNDER_REVIEW": "Waiting for guide approval",
        "CHANGES_REQUIRED": "Edit & Resubmit",
        "APPROVED": "Continue to next level",
        "LOCKED": "View",
    }
    next_label = labels.get(current_status, current_status)
    if (
        current_status == "APPROVED"
        and not is_granted
        and current_stage
        and current_stage.order == 0
    ):
        next_label = "Your information has been approved. Waiting for your guide to grant access to the next stage."
    return {
        "group_id": group.id,
        "current_level_order": current_stage.order if current_stage else 0,
        "current_level_name": current_stage.name if current_stage else "Completed",
        "current_level_status": current_status,
        "is_access_granted": is_granted,
        "next_action_label": next_label,
        "stage_id": current_stage.id if current_stage else None,
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def stage_status(request, group_id):
    group = get_object_or_404(ProjectGroup, id=group_id)
    stages = ProjectStage.objects.filter(academic_year=group.academic_year).order_by(
        "order"
    )
    if not stages.exists():
        stages = ProjectStage.objects.all().order_by("order")
    data = []
    for s in stages:
        sub = (
            Submission.objects.filter(section__stage=s, group=group)
            .order_by("-created_at")
            .first()
        )
        data.append(
            {
                "stage": s.name,
                "slug": s.slug,
                "order": s.order,
                "status": sub.status if sub else "not_started",
                "id": s.id,
            }
        )
    return Response({"success": True, "data": data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def group_level(request, group_id):
    group = get_object_or_404(ProjectGroup, id=group_id)
    if (
        request.user.role == "student"
        and not group.members.filter(student=request.user).exists()
    ):
        return Response({"success": False, "message": "Not your group"}, status=403)
    if request.user.role in ["faculty", "reviewer"] and request.user.role != "hod":
        if (
            not group.guide_assignments.filter(faculty=request.user).exists()
            and not group.reviewer_assignments.filter(faculty=request.user).exists()
        ):
            if not group.members.filter(student=request.user).exists():
                return Response(
                    {"success": False, "message": "Not assigned to this group"},
                    status=403,
                )
    data = compute_level(group)
    stages = ProjectStage.objects.filter(academic_year=group.academic_year).order_by(
        "order"
    )
    if not stages.exists():
        stages = ProjectStage.objects.all().order_by("order")
    levels = []
    for s in stages:
        ag = AccessGrant.objects.filter(group=group, stage=s).first()
        sub = (
            Submission.objects.filter(group=group, section__stage=s)
            .order_by("-created_at")
            .first()
        )
        levels.append(
            {
                "order": s.order,
                "name": s.name,
                "slug": s.slug,
                "id": s.id,
                "status": sub.status.upper() if sub else "NOT_STARTED",
                "granted": ag.granted if ag else (True if s.order == 0 else False),
                "granted_at": ag.granted_at if ag else None,
            }
        )
    data["levels"] = levels
    return Response({"success": True, "data": data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def access_grant(request, group_id, stage_id):
    group = get_object_or_404(ProjectGroup, id=group_id)
    stage = get_object_or_404(ProjectStage, id=stage_id)
    if request.user.role not in ["faculty", "reviewer", "hod", "admin"]:
        return Response(
            {"success": False, "message": "Only Guide/Reviewer/HOD can grant access"},
            status=403,
        )
    if request.user.role in ["faculty", "reviewer"]:
        if (
            not group.guide_assignments.filter(faculty=request.user).exists()
            and not group.reviewer_assignments.filter(faculty=request.user).exists()
        ):
            return Response(
                {"success": False, "message": "Not assigned to this group"}, status=403
            )
    granted = request.data.get("granted", True)
    remark = request.data.get("remark", "")
    from django.utils import timezone
    from apps.audit.models import AuditLog

    obj, created = AccessGrant.objects.get_or_create(
        group=group,
        stage=stage,
        defaults={
            "granted_by": request.user,
            "granted": bool(granted),
            "remark": remark,
            "granted_at": timezone.now() if granted else None,
        },
    )
    if not created:
        obj.granted = bool(granted)
        obj.remark = remark
        obj.granted_by = request.user
        if granted:
            obj.granted_at = timezone.now()
            obj.revoked_at = None
        else:
            obj.revoked_at = timezone.now()
        obj.save()
    AuditLog.objects.create(
        actor=request.user,
        actor_role=request.user.role,
        action="stage_unlocked" if granted else "stage_locked",
        entity_type="access_grant",
        entity_id=obj.id,
        new_value={"group": group.id, "stage": stage.id, "granted": bool(granted)},
    )
    from .serializers import AccessGrantSerializer

    return Response({"success": True, "data": AccessGrantSerializer(obj).data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def guide_queue(request):
    from apps.groups.models import ProjectGuideAssignment, ReviewerAssignment

    if request.user.role not in ["faculty", "reviewer", "hod", "admin"]:
        return Response({"success": False, "message": "Not authorized"}, status=403)
    groups = (
        ProjectGroup.objects.filter(guide_assignments__faculty=request.user).distinct()
        | ProjectGroup.objects.filter(
            reviewer_assignments__faculty=request.user
        ).distinct()
    )
    if request.user.role in ["hod", "admin"]:
        groups = ProjectGroup.objects.all()
    data = []
    for g in groups:
        lvl = compute_level(g)
        pending_data = Submission.objects.filter(
            group=g, status__in=["submitted", "under_review"]
        ).exists()
        ag = AccessGrant.objects.filter(group=g, stage__order=1).first()
        need_grant = (
            lvl["current_level_order"] == 0
            and lvl["current_level_status"] == "APPROVED"
            and not (ag.granted if ag else False)
        )
        data.append(
            {
                "group_id": g.id,
                "group_number": g.group_number,
                "level": lvl,
                "needs_data_approval": pending_data,
                "needs_access_grant": need_grant,
            }
        )
    return Response({"success": True, "data": data})
