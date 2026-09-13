from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError, NotFound
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.conf import settings
import os, mimetypes

from apps.common.permissions import IsStudent, IsHOD
from apps.accounts.models import StudentProfile
from apps.accounts.serializers import StudentProfileSerializer
from apps.groups.models import ProjectGroup, GroupMember
from apps.groups.serializers import GroupProfileSerializer
from apps.submissions.models import Submission, SubmissionVersion
from apps.submissions.serializers import (
    SubmissionSerializer,
    SubmissionVersionSerializer,
)
from apps.documents.models import Document, DocumentVersion
from apps.documents.serializers import DocumentSerializer, DocumentVersionSerializer
from apps.reviews.models import Review, Mark
from apps.reviews.serializers import ReviewSerializer, MarkSerializer
from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer
from apps.audit.models import AuditLog, Deadline
from apps.audit.serializers import AuditLogSerializer
from apps.projects.models import ProjectStage, Section


def _get_student_group(user):
    if not user or not user.is_authenticated:
        return None
    membership = (
        GroupMember.objects.filter(student=user, status="accepted", is_active=True)
        .select_related("group")
        .first()
    )
    if membership:
        return membership.group
    return (
        ProjectGroup.objects.filter(members__student=user, members__status="accepted")
        .distinct()
        .first()
    )


def _ensure_student(user):
    if user.role != "student":
        raise PermissionDenied("Student role required")
    return _get_student_group(user)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard(request):
    if request.user.role != "student":
        return Response({"success": False, "message": "Student only"}, status=403)
    group = _get_student_group(request.user)
    if not group:
        return Response(
            {
                "success": True,
                "data": {
                    "has_group": False,
                    "welcome": request.user.first_name or request.user.username,
                    "group": None,
                    "project": None,
                    "guide": None,
                    "progress": 0,
                    "stats": {
                        "total_log_entries": 0,
                        "pending_verification": 0,
                        "approved_entries": 0,
                        "changes_requested": 0,
                        "documents_submitted": 0,
                        "overall_progress": 0,
                    },
                    "current_stage": None,
                    "current_milestone": None,
                    "last_submission": None,
                    "next_deadline": None,
                    "pending_actions": ["Create or join a group"],
                },
            }
        )
    from apps.documents.models import Document

    subs = Submission.objects.filter(group=group)
    stats = {
        "total_log_entries": subs.count(),
        "pending_verification": subs.filter(
            status__in=["submitted", "under_review", "resubmitted"]
        ).count(),
        "approved_entries": subs.filter(status__in=["approved", "locked"]).count(),
        "changes_requested": subs.filter(status="changes_required").count(),
        "documents_submitted": Document.objects.filter(group=group).count(),
        "overall_progress": group.progress,
    }
    guide = group.guide_assignments.filter(is_active=True).first()
    guide_data = None
    if guide:
        try:
            prof = guide.faculty.faculty_profile
            guide_data = {
                "name": prof.name,
                "email": guide.faculty.email,
                "designation": prof.designation,
                "department": prof.department,
            }
        except:
            guide_data = {"name": guide.faculty.username, "email": guide.faculty.email}
    # current stage: first non-locked/approved stage else last
    stages = list(
        ProjectStage.objects.filter(academic_year=group.academic_year).order_by("order")
    )
    if not stages:
        stages = list(ProjectStage.objects.all().order_by("order"))
    current_stage = None
    for s in stages:
        sub = (
            Submission.objects.filter(group=group, section__stage=s)
            .order_by("-created_at")
            .first()
        )
        if not sub or sub.status not in ["approved", "locked"]:
            current_stage = {
                "id": s.id,
                "name": s.name,
                "slug": s.slug,
                "order": s.order,
                "status": sub.status if sub else "not_started",
            }
            break
    if not current_stage and stages:
        s = stages[-1]
        sub = (
            Submission.objects.filter(group=group, section__stage=s)
            .order_by("-created_at")
            .first()
        )
        current_stage = {
            "id": s.id,
            "name": s.name,
            "slug": s.slug,
            "order": s.order,
            "status": sub.status if sub else "not_started",
        }
    last_sub = subs.order_by("-submitted_at", "-created_at").first()
    next_deadline = None
    dl = (
        Deadline.objects.filter(academic_year=group.academic_year, is_active=True)
        .order_by("due_date")
        .first()
    )
    if dl:
        next_deadline = {
            "stage": dl.stage.name,
            "due_date": dl.due_date,
            "status": "overdue" if dl.due_date < timezone.localdate() else "upcoming",
        }
    pending = []
    if subs.filter(status="changes_required").exists():
        pending.append("Address changes requested by faculty")
    if subs.filter(status="draft").exists():
        pending.append("Submit draft entries")
    if not subs.exists():
        pending.append("Create first log entry")
    elif current_stage and current_stage["status"] in ["not_started", "draft"]:
        pending.append(f"Submit weekly log entry for {current_stage['name']}")
    profile = None
    try:
        profile = request.user.student_profile
    except:
        pass
    return Response(
        {
            "success": True,
            "data": {
                "has_group": True,
                "welcome": profile.name
                if profile and profile.name
                else request.user.first_name or request.user.username,
                "group": {
                    "id": group.id,
                    "group_number": group.group_number,
                    "academic_year": group.academic_year.year_label
                    if group.academic_year
                    else "",
                    "department": group.department.name if group.department else "",
                },
                "project": {
                    "title": group.project.title if group.project else "",
                    "domain": group.project.area_domain if group.project else "",
                }
                if group.project
                else None,
                "guide": guide_data,
                "progress": group.progress,
                "stats": stats,
                "current_stage": current_stage,
                "last_submission": SubmissionSerializer(last_sub).data
                if last_sub
                else None,
                "next_deadline": next_deadline,
                "pending_actions": pending,
            },
        }
    )


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def profile_view(request):
    if request.user.role != "student":
        return Response({"success": False, "message": "Student only"}, status=403)
    try:
        prof = request.user.student_profile
    except StudentProfile.DoesNotExist:
        if request.method == "GET":
            return Response(
                {
                    "success": True,
                    "data": {
                        "user": {
                            "id": request.user.id,
                            "email": request.user.email,
                            "username": request.user.username,
                            "role": request.user.role,
                        },
                        "profile": None,
                    },
                }
            )
        # create on PATCH
        prof = None
    if request.method == "GET":
        user_data = {
            "id": request.user.id,
            "email": request.user.email,
            "username": request.user.username,
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "role": request.user.role,
        }
        prof_data = StudentProfileSerializer(prof).data if prof else None
        return Response(
            {"success": True, "data": {"user": user_data, "profile": prof_data}}
        )
    # PATCH
    data = (
        request.data if request.content_type != "multipart/form-data" else request.data
    )
    allowed = {
        "name",
        "roll_number",
        "mobile",
        "exam_seat_number",
        "email",
        "department",
        "photograph",
    }
    # block role change
    if "role" in data:
        return Response(
            {
                "success": False,
                "message": "Role change not allowed",
                "errors": {"role": ["Cannot change role"]},
            },
            status=403,
        )
    if "is_active" in data or "is_staff" in data or "is_superuser" in data:
        return Response({"success": False, "message": "Not allowed"}, status=403)
    if not prof:
        # create profile
        from django.contrib.auth import get_user_model

        User = get_user_model()
        payload = {k: v for k, v in data.items() if k in allowed}
        if "roll_number" not in payload or not payload["roll_number"]:
            payload["roll_number"] = f"4100{request.user.id:04d}"
        if "name" not in payload:
            payload["name"] = request.user.username
        payload["user"] = request.user.id
        s = StudentProfileSerializer(data=payload)
        s.is_valid(raise_exception=True)
        obj = s.save(user=request.user)
        if "email" in payload and payload["email"] != request.user.email:
            if (
                User.objects.filter(email=payload["email"])
                .exclude(id=request.user.id)
                .exists()
            ):
                return Response(
                    {"success": False, "message": "Email already exists"}, status=400
                )
            request.user.email = payload["email"]
            request.user.username = payload["email"].split("@")[0]
            request.user.save(update_fields=["email", "username"])
        AuditLog.objects.create(
            actor=request.user,
            actor_role=request.user.role,
            action="submission_edited",
            entity_type="student_profile",
            entity_id=obj.id,
            new_value={"created": True},
        )
        return Response({"success": True, "data": StudentProfileSerializer(obj).data})
    # filter only allowed
    update_data = {k: v for k, v in data.items() if k in allowed}
    if not update_data:
        return Response(
            {
                "success": False,
                "message": "No editable fields provided",
                "errors": {
                    "fields": [
                        "Only name,roll_number,mobile,exam_seat_number,email,department,photograph editable"
                    ]
                },
            },
            status=400,
        )
    # handle file
    if "photograph" in request.FILES:
        f = request.FILES["photograph"]
        if f.size > 5 * 1024 * 1024:
            return Response(
                {"success": False, "message": "Photo must be <5MB"}, status=400
            )
        if not f.content_type.startswith("image/"):
            return Response(
                {"success": False, "message": "Invalid photo type"}, status=400
            )
        update_data["photograph"] = f
    # validate email uniqueness
    if "email" in update_data and update_data["email"] != request.user.email:
        from django.contrib.auth import get_user_model

        User = get_user_model()
        if (
            User.objects.filter(email=update_data["email"])
            .exclude(id=request.user.id)
            .exists()
        ):
            return Response(
                {"success": False, "message": "Email already exists"}, status=400
            )
    old = dict(StudentProfileSerializer(prof).data) if prof else {}
    s = StudentProfileSerializer(prof, data=update_data, partial=True)
    s.is_valid(raise_exception=True)
    obj = s.save()
    if "email" in update_data and update_data["email"] != request.user.email:
        request.user.email = update_data["email"]
        request.user.username = update_data["email"].split("@")[0]
        request.user.save(update_fields=["email", "username"])
    AuditLog.objects.create(
        actor=request.user,
        actor_role=request.user.role,
        action="submission_edited",
        entity_type="student_profile",
        entity_id=obj.id,
        previous_value=old,
        new_value=update_data,
    )
    return Response(
        {
            "success": True,
            "data": StudentProfileSerializer(obj).data,
            "message": "Profile updated",
        }
    )


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def group_view(request):
    if request.user.role != "student":
        return Response({"success": False, "message": "Student only"}, status=403)
    group = _get_student_group(request.user)
    if not group:
        return Response({"success": False, "message": "No group found"}, status=404)
    if request.method == "GET":
        data = GroupProfileSerializer(group).data
        from apps.groups.views import _can_edit_group

        data["can_edit"] = _can_edit_group(request.user, group)
        data["is_locked"] = group.is_locked
        return Response({"success": True, "data": data})
    # PATCH: delegate to existing logic but restrict
    from apps.groups.views import _can_edit_group

    if not _can_edit_group(request.user, group):
        if group.is_locked:
            return Response(
                {"success": False, "message": "Group is locked"}, status=423
            )
        return Response(
            {"success": False, "message": "Only members can edit"}, status=403
        )
    data = request.data
    errors = {}
    project_fields = {}
    if "project_title" in data or "title" in data:
        project_fields["title"] = (
            data.get("project_title") or data.get("title") or ""
        ).strip()
        if not project_fields["title"]:
            errors["project_title"] = ["Title required"]
        elif len(project_fields["title"]) < 5:
            errors["project_title"] = ["Title must be >=5 chars"]
    if "area_domain" in data or "area" in data:
        project_fields["area_domain"] = (
            data.get("area_domain") or data.get("area") or ""
        ).strip()
        if not project_fields["area_domain"]:
            errors["area_domain"] = ["Domain required"]
    if "description" in data:
        project_fields["description"] = (data.get("description") or "").strip()
    if "technology_stack" in data:
        project_fields["technology_stack"] = (
            data.get("technology_stack") or ""
        ).strip()
    if errors:
        return Response(
            {"success": False, "message": "Validation failed", "errors": errors},
            status=400,
        )
    prev = {}
    if group.project:
        prev = {"title": group.project.title, "area_domain": group.project.area_domain}
    if project_fields and group.project:
        for k, v in project_fields.items():
            setattr(group.project, k, v)
        group.project.save()
    elif project_fields and not group.project:
        from apps.projects.models import Project

        project = Project.objects.create(
            title=project_fields.get("title", "Untitled"),
            area_domain=project_fields.get("area_domain", ""),
            description=project_fields.get("description", ""),
            technology_stack=project_fields.get("technology_stack", ""),
            academic_year=group.academic_year,
            created_by=request.user,
        )
        group.project = project
        group.save(update_fields=["project"])
    group.updated_by = request.user
    group.save(update_fields=["updated_at", "updated_by"])
    AuditLog.objects.create(
        actor=request.user,
        actor_role=request.user.role,
        action="submission_edited",
        entity_type="project_group",
        entity_id=group.id,
        previous_value=prev,
        new_value=project_fields,
    )
    data_out = GroupProfileSerializer(group).data
    data_out["can_edit"] = True
    return Response({"success": True, "data": data_out, "message": "Group updated"})


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def logbook_list_create(request):
    if request.user.role != "student":
        return Response({"success": False, "message": "Student only"}, status=403)
    group = _get_student_group(request.user)
    if not group:
        return Response({"success": False, "message": "No group"}, status=404)
    if request.method == "GET":
        qs = (
            Submission.objects.filter(group=group)
            .select_related("section__stage", "submitted_by", "reviewed_by")
            .order_by("-created_at")
        )
        # also include Section-based drafts without submission?
        data = SubmissionSerializer(qs, many=True).data
        # enrich with week/date from content
        return Response({"success": True, "data": data})
    # POST create draft
    d = request.data
    # support JSON and multipart
    week = d.get("week") or d.get("week_number")
    date_val = d.get("date")
    stage_id = d.get("stage") or d.get("stage_id") or d.get("project_stage")
    title = d.get("title") or d.get("project_stage_name") or "Log Entry"
    content = d.get("content")
    if isinstance(content, str):
        import json

        try:
            content = json.loads(content)
        except:
            content = {"text": content}
    if not content:
        content = {
            "week": week,
            "date": date_val,
            "project_stage": d.get("project_stage") or d.get("stage_name") or "",
            "work_completed": d.get("work_completed") or d.get("workCompleted") or "",
            "work_planned": d.get("work_planned") or d.get("workPlanned") or "",
            "problems": d.get("problems") or d.get("challenges") or "",
            "solution": d.get("solution") or d.get("action_taken") or "",
            "learning": d.get("learning") or d.get("outcome") or "",
            "evidence": d.get("evidence") or "",
        }
        # merge extra fields
        for k in [
            "week",
            "date",
            "project_stage",
            "work_completed",
            "work_planned",
            "problems",
            "solution",
            "learning",
        ]:
            if d.get(k) and k not in content:
                content[k] = d.get(k)
    # resolve stage: if provided use it else default to first incomplete
    stage = None
    if stage_id:
        try:
            stage = ProjectStage.objects.get(id=stage_id)
            if stage.academic_year_id != group.academic_year_id:
                # allow but not error
                pass
        except ProjectStage.DoesNotExist:
            return Response({"success": False, "message": "Invalid stage"}, status=400)
    else:
        # find current incomplete stage
        stages = list(
            ProjectStage.objects.filter(academic_year=group.academic_year).order_by(
                "order"
            )
        )
        for s in stages:
            sub = (
                Submission.objects.filter(group=group, section__stage=s)
                .order_by("-created_at")
                .first()
            )
            if not sub or sub.status in ["draft", "changes_required"]:
                stage = s
                break
        if not stage:
            stage = (
                ProjectStage.objects.filter(academic_year=group.academic_year)
                .order_by("order")
                .first()
            )
        if not stage:
            return Response(
                {"success": False, "message": "No stages configured"}, status=400
            )
    # create section if not exists
    sec, _ = Section.objects.get_or_create(
        group=group,
        stage=stage,
        section_type=stage.slug,
        defaults={
            "title": stage.name,
            "owner_role": "student",
            "content": content,
            "status": "draft",
        },
    )
    # check access grant: first stage (min order, typically 1) does not need grant; later stages do
    if stage.order > 1:
        from apps.workflow.models import AccessGrant

        ag = AccessGrant.objects.filter(group=group, stage__order=1).first()
        if not ag or not ag.granted:
            return Response(
                {
                    "success": False,
                    "message": "Level 1 locked — complete Information and wait for guide grant",
                    "errors": {"access": ["Not granted"]},
                },
                status=403,
            )
        if stage.order > 1:
            prev = ProjectStage.objects.filter(
                academic_year=stage.academic_year, order=stage.order - 1
            ).first()
            if prev:
                sub = (
                    Submission.objects.filter(group=group, section__stage=prev)
                    .order_by("-created_at")
                    .first()
                )
                if not sub or sub.status not in ["approved", "locked"]:
                    return Response(
                        {
                            "success": False,
                            "message": f"Previous level {prev.name} not complete",
                            "errors": {
                                "level": [
                                    f"Current {sub.status if sub else 'NOT_STARTED'}"
                                ]
                            },
                        },
                        status=403,
                    )
    # handle file evidence
    evidence_files = []
    for f in request.FILES.getlist("evidence") or request.FILES.getlist("files") or []:
        if f.size > 10 * 1024 * 1024:
            return Response(
                {"success": False, "message": f"File {f.name} exceeds 10MB"}, status=400
            )
        allowed_ext = {".pdf", ".png", ".jpg", ".jpeg", ".doc", ".docx", ".txt"}
        ext = os.path.splitext(f.name)[1].lower()
        if ext not in allowed_ext:
            return Response(
                {"success": False, "message": f"Invalid file type {ext}"}, status=400
            )
        mime, _ = mimetypes.guess_type(f.name)
        if mime and mime not in [
            "application/pdf",
            "image/png",
            "image/jpeg",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
        ]:
            return Response(
                {"success": False, "message": f"Invalid MIME {mime}"}, status=400
            )
        path = default_storage.save(f"logbook/group_{group.id}/{f.name}", f)
        evidence_files.append(path)
    if evidence_files:
        content["evidence_files"] = evidence_files
    # create submission
    # validate week duplicate? allow
    sub = Submission.objects.create(
        section=sec,
        group=group,
        submitted_by=request.user,
        content=content,
        status="draft",
        version=1,
    )
    sec.content = content
    sec.status = "draft"
    sec.save()
    AuditLog.objects.create(
        actor=request.user,
        actor_role=request.user.role,
        action="submission_created",
        entity_type="submission",
        entity_id=sub.id,
        new_value={"group": group.id, "stage": stage.id},
    )
    return Response(
        {"success": True, "data": SubmissionSerializer(sub).data}, status=201
    )


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def logbook_detail(request, pk):
    if request.user.role != "student":
        return Response({"success": False, "message": "Student only"}, status=403)
    group = _get_student_group(request.user)
    sub = get_object_or_404(Submission, id=pk, group=group)
    if request.method == "GET":
        data = SubmissionSerializer(sub).data
        versions = SubmissionVersion.objects.filter(submission=sub).order_by(
            "version_number"
        )
        data["versions"] = SubmissionVersionSerializer(versions, many=True).data
        return Response({"success": True, "data": data})
    if request.method == "DELETE":
        if sub.status != "draft":
            return Response(
                {"success": False, "message": "Only drafts can be deleted"}, status=403
            )
        # verify ownership
        if (
            sub.submitted_by_id != request.user.id
            and not GroupMember.objects.filter(
                group=group, student=request.user
            ).exists()
        ):
            return Response(
                {"success": False, "message": "Not your submission"}, status=403
            )
        sub.delete()
        AuditLog.objects.create(
            actor=request.user,
            actor_role=request.user.role,
            action="submission_edited",
            entity_type="submission",
            entity_id=pk,
            new_value={"deleted": True},
        )
        return Response({"success": True, "message": "Draft deleted"})
    # PATCH
    if sub.status not in ["draft", "changes_required"]:
        return Response(
            {
                "success": False,
                "message": f"Cannot edit submission in {sub.status} status. Only DRAFT or CHANGES_REQUESTED editable",
            },
            status=403,
        )
    data = request.data
    content = data.get("content")
    if content and isinstance(content, str):
        import json

        try:
            content = json.loads(content)
        except:
            content = {"text": content}
    if not content:
        # merge fields
        existing = sub.content or {}
        for k in [
            "week",
            "date",
            "project_stage",
            "work_completed",
            "work_planned",
            "problems",
            "solution",
            "learning",
        ]:
            if data.get(k) is not None:
                existing[k] = data.get(k)
        # also handle alternate names
        mapping = {
            "workCompleted": "work_completed",
            "workPlanned": "work_planned",
            "action_taken": "solution",
            "challenges": "problems",
            "outcome": "learning",
        }
        for src, dst in mapping.items():
            if data.get(src):
                existing[dst] = data.get(src)
        if data.get("evidence"):
            existing["evidence"] = data.get("evidence")
        content = existing
    # handle files
    evidence_files = (
        content.get("evidence_files", []) if isinstance(content, dict) else []
    )
    for f in request.FILES.getlist("evidence") or request.FILES.getlist("files") or []:
        if f.size > 10 * 1024 * 1024:
            return Response({"success": False, "message": "File too large"}, status=400)
        ext = os.path.splitext(f.name)[1].lower()
        if ext not in {".pdf", ".png", ".jpg", ".jpeg", ".doc", ".docx", ".txt"}:
            return Response({"success": False, "message": "Invalid type"}, status=400)
        path = default_storage.save(f"logbook/group_{group.id}/{f.name}", f)
        evidence_files.append(path)
    if evidence_files:
        content["evidence_files"] = evidence_files
    # save version before edit if changes_required
    if sub.status == "changes_required":
        # snapshot current as version
        SubmissionVersion.objects.create(
            submission=sub,
            version_number=sub.version,
            content=sub.content,
            review_remark=sub.review_remarks,
            submitted_by=sub.submitted_by,
        )
    sub.content = content
    sub.save()
    if sub.section:
        sub.section.content = content
        sub.section.save(update_fields=["content"])
    AuditLog.objects.create(
        actor=request.user,
        actor_role=request.user.role,
        action="submission_edited",
        entity_type="submission",
        entity_id=sub.id,
        new_value={"edited": True},
    )
    return Response({"success": True, "data": SubmissionSerializer(sub).data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logbook_submit(request, pk):
    if request.user.role != "student":
        return Response({"success": False, "message": "Student only"}, status=403)
    group = _get_student_group(request.user)
    sub = get_object_or_404(Submission, id=pk, group=group)
    if sub.status not in ["draft", "changes_required", "resubmitted"]:
        return Response(
            {"success": False, "message": f"Cannot submit from status {sub.status}"},
            status=400,
        )
    # if changes_required must have been edited
    if sub.status == "draft":
        sub.status = "submitted"
    elif sub.status == "changes_required":
        sub.status = "resubmitted"
        # also create version snapshot
        SubmissionVersion.objects.create(
            submission=sub,
            version_number=sub.version,
            content=sub.content,
            submitted_by=request.user,
        )
        sub.version += 1
    else:
        sub.status = "submitted"
    sub.submitted_at = timezone.now()
    sub.save()
    if sub.section:
        sub.section.status = "submitted"
        sub.section.submitted_at = timezone.now()
        sub.section.save(update_fields=["status", "submitted_at"])
    from apps.notifications.models import Notification

    notified = False
    for ga in sub.group.guide_assignments.filter(is_active=True):
        Notification.objects.create(
            recipient=ga.faculty,
            notification_type="submission",
            title="Log entry submitted for review",
            message=f"Group {group.group_number} submitted {sub.section.stage.name} — Week {sub.content.get('week', '')}",
            related_type="submission",
            related_id=sub.id,
        )
        notified = True
    for ra in sub.group.reviewer_assignments.filter(is_active=True):
        Notification.objects.create(
            recipient=ra.faculty,
            notification_type="submission",
            title="Log entry submitted",
            message=f"Group {group.group_number} submitted entry",
            related_type="submission",
            related_id=sub.id,
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
                message=f"Group {group.group_number} submitted — no guide assigned",
                related_type="submission",
                related_id=sub.id,
            )
    AuditLog.objects.create(
        actor=request.user,
        actor_role=request.user.role,
        action="submission_submitted",
        entity_type="submission",
        entity_id=sub.id,
        new_value={"status": sub.status},
    )
    return Response({"success": True, "data": SubmissionSerializer(sub).data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def progress_view(request):
    if request.user.role != "student":
        return Response({"success": False, "message": "Student only"}, status=403)
    group = _get_student_group(request.user)
    if not group:
        return Response({"success": False, "message": "No group"}, status=404)
    stages = list(
        ProjectStage.objects.filter(academic_year=group.academic_year).order_by("order")
    )
    if not stages:
        stages = list(ProjectStage.objects.all().order_by("order"))
    result = []
    for s in stages:
        sub = (
            Submission.objects.filter(group=group, section__stage=s)
            .order_by("-created_at")
            .first()
        )
        sec = Section.objects.filter(group=group, stage=s).first()
        dl = Deadline.objects.filter(stage=s, academic_year=group.academic_year).first()
        status_val = sub.status if sub else "not_started"
        pct = (
            100
            if status_val in ["approved", "locked"]
            else 50
            if status_val in ["submitted", "under_review", "resubmitted"]
            else 25
            if status_val == "changes_required"
            else 0
        )
        review = Review.objects.filter(group=group, stage=s).first()
        result.append(
            {
                "id": s.id,
                "name": s.name,
                "order": s.order,
                "slug": s.slug,
                "is_required": s.is_required,
                "status": status_val,
                "progress_pct": pct,
                "start_date": dl.start_date if dl else None,
                "target_date": dl.due_date if dl else s.due_date,
                "completion_pct": pct,
                "submission": SubmissionSerializer(sub).data if sub else None,
                "feedback": sub.review_remarks if sub else "",
                "deadline_status": "overdue"
                if dl
                and dl.due_date < timezone.localdate()
                and status_val not in ["approved", "locked"]
                else "upcoming"
                if dl
                else None,
                "marks": None,
            }
        )
    upcoming = []
    for s in stages:
        dl = Deadline.objects.filter(stage=s, academic_year=group.academic_year).first()
        if dl:
            stat = (
                "overdue"
                if dl.due_date < timezone.localdate()
                else "due_today"
                if dl.due_date == timezone.localdate()
                else "upcoming"
            )
            sub = Submission.objects.filter(group=group, section__stage=s).first()
            completed = sub and sub.status in ["approved", "locked"]
            upcoming.append(
                {
                    "name": s.name,
                    "due": dl.due_date,
                    "status": "completed" if completed else stat,
                }
            )
    return Response(
        {
            "success": True,
            "data": {
                "stages": result,
                "milestones": upcoming,
                "overall_progress": group.progress,
            },
        }
    )


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def documents_view(request):
    if request.user.role != "student":
        return Response({"success": False, "message": "Student only"}, status=403)
    group = _get_student_group(request.user)
    if not group:
        return Response({"success": False, "message": "No group"}, status=404)
    if request.method == "GET":
        qs = Document.objects.filter(group=group).order_by("-created_at")
        data = DocumentSerializer(qs, many=True).data
        # attach versions
        for d in data:
            vers = DocumentVersion.objects.filter(document_id=d["id"]).order_by(
                "version_number"
            )
            d["versions"] = DocumentVersionSerializer(vers, many=True).data
        return Response({"success": True, "data": data})
    # POST upload
    title = request.data.get("title") or request.data.get("name") or ""
    doc_type = request.data.get("doc_type") or request.data.get("type") or "other"
    file = request.FILES.get("file") or request.FILES.get("document")
    if not file:
        return Response(
            {
                "success": False,
                "message": "File required",
                "errors": {"file": ["Required"]},
            },
            status=400,
        )
    if not title:
        title = file.name
    if file.size > 10 * 1024 * 1024:
        return Response({"success": False, "message": "File exceeds 10MB"}, status=400)
    allowed = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".ppt": "application/vnd.ms-powerpoint",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".txt": "text/plain",
        ".zip": "application/zip",
    }
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in allowed:
        return Response(
            {"success": False, "message": f"Invalid file extension {ext}"}, status=400
        )
    mime, _ = mimetypes.guess_type(file.name)
    # mime check not strict but validate
    if file.content_type not in [
        "application/pdf",
        "image/png",
        "image/jpeg",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "text/plain",
        "application/zip",
        "application/octet-stream",
    ]:
        # allow octet-stream for some browsers
        pass
    # check existing doc with same title+type -> versioning
    existing = Document.objects.filter(
        group=group, title=title, doc_type=doc_type
    ).first()
    path = default_storage.save(f"documents/group_{group.id}/{file.name}", file)
    if existing:
        # create version
        DocumentVersion.objects.create(
            document=existing,
            version_number=existing.current_version,
            file_path=existing.file_path,
            file_size=existing.file_size or 0,
            mime_type=existing.mime_type,
            uploaded_by=existing.uploaded_by,
        )
        existing.file_path = path
        existing.file_size = file.size
        existing.mime_type = file.content_type
        existing.current_version += 1
        existing.uploaded_by = request.user
        existing.save()
        AuditLog.objects.create(
            actor=request.user,
            actor_role=request.user.role,
            action="document_replaced",
            entity_type="document",
            entity_id=existing.id,
            new_value={"version": existing.current_version},
        )
        return Response(
            {
                "success": True,
                "data": DocumentSerializer(existing).data,
                "message": "New version uploaded",
            },
            status=201,
        )
    doc = Document.objects.create(
        group=group,
        doc_type=doc_type,
        title=title,
        uploaded_by=request.user,
        file_path=path,
        file_size=file.size,
        mime_type=file.content_type,
        stage_id=request.data.get("stage") or None,
    )
    # create first version
    DocumentVersion.objects.create(
        document=doc,
        version_number=1,
        file_path=path,
        file_size=file.size,
        mime_type=file.content_type,
        uploaded_by=request.user,
    )
    AuditLog.objects.create(
        actor=request.user,
        actor_role=request.user.role,
        action="document_uploaded",
        entity_type="document",
        entity_id=doc.id,
        new_value={"title": title},
    )
    return Response({"success": True, "data": DocumentSerializer(doc).data}, status=201)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def document_versions(request, pk):
    if request.user.role != "student":
        return Response({"success": False, "message": "Student only"}, status=403)
    group = _get_student_group(request.user)
    doc = get_object_or_404(Document, id=pk, group=group)
    vers = DocumentVersion.objects.filter(document=doc).order_by("version_number")
    return Response(
        {"success": True, "data": DocumentVersionSerializer(vers, many=True).data}
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def reviews_view(request):
    if request.user.role != "student":
        return Response({"success": False, "message": "Student only"}, status=403)
    group = _get_student_group(request.user)
    if not group:
        return Response({"success": False, "message": "No group"}, status=404)
    reviews = Review.objects.filter(group=group).order_by("review_number")
    data = []
    total_obt = 0
    total_max = 0
    for r in reviews:
        ser = ReviewSerializer(r).data
        # only show marks if finalized or requested
        if r.status == "finalized":
            marks = Mark.objects.filter(group=group, criterion__review=r)
            ser["marks"] = MarkSerializer(marks, many=True).data
            ser["total_obtained"] = str(r.total_obtained_marks)
            ser["total_max"] = str(r.total_max_marks)
            try:
                total_obt += float(r.total_obtained_marks)
                total_max += float(r.total_max_marks)
            except:
                pass
        else:
            ser["marks"] = (
                []
                if r.status != "finalized"
                else MarkSerializer(
                    Mark.objects.filter(group=group, criterion__review=r), many=True
                ).data
            )
            # hide marks if not finalized
            if r.status != "finalized":
                ser["marks_hidden"] = True
        # approvals
        from apps.reviews.models import Approval

        # use submission approvals if exists
        ser["reviewer_comments"] = r.overall_remarks
        data.append(ser)
    # also include submission approvals
    submissions = Submission.objects.filter(group=group).order_by("-submitted_at")
    feedbacks = []
    for s in submissions:
        if s.review_remarks:
            feedbacks.append(
                {
                    "stage": s.section.stage.name
                    if s.section and s.section.stage
                    else "",
                    "status": s.status,
                    "reviewed_by": s.reviewed_by.email if s.reviewed_by else "",
                    "reviewed_at": s.reviewed_at,
                    "comment": s.review_remarks,
                }
            )
    return Response(
        {
            "success": True,
            "data": {
                "reviews": data,
                "feedbacks": feedbacks,
                "total": {"obtained": total_obt, "max": total_max},
            },
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def notifications_view(request):
    if request.user.role != "student":
        return Response({"success": False, "message": "Student only"}, status=403)
    qs = Notification.objects.filter(recipient=request.user).order_by("-created_at")
    is_read = request.query_params.get("is_read")
    if is_read in ["true", "false"]:
        qs = qs.filter(is_read=(is_read == "true"))
    data = NotificationSerializer(qs, many=True).data
    unread = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return Response({"success": True, "data": data, "unread_count": unread})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def notification_read(request, pk):
    n = get_object_or_404(Notification, id=pk, recipient=request.user)
    n.is_read = True
    n.read_at = timezone.now()
    n.save()
    return Response({"success": True, "data": NotificationSerializer(n).data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def notifications_mark_all(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(
        is_read=True, read_at=timezone.now()
    )
    return Response({"success": True})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def final_logbook_view(request):
    if request.user.role != "student":
        return Response({"success": False, "message": "Student only"}, status=403)
    group = _get_student_group(request.user)
    if not group:
        return Response({"success": False, "message": "No group"}, status=404)
    from apps.logbook.views import _check_conditions
    from apps.logbook.models import FinalLogBook

    errors = _check_conditions(group)
    checklist = {
        "group_information": bool(group.group_number and group.project),
        "student_information": GroupMember.objects.filter(
            group=group, status="accepted"
        ).count()
        >= 1,
        "project_information": bool(group.project and group.project.title),
        "log_entries": Submission.objects.filter(group=group).exists(),
        "faculty_verification": not bool(
            [e for e in errors.get("stages", []) if "not yet LOCKED" in str(e)]
        )
        if errors
        else True,
        "reviewer_verification": "reviews" not in errors,
        "required_documents": Document.objects.filter(group=group).exists(),
        "progress_information": group.progress > 0,
        "final_review": "hod_approval" not in errors,
    }
    # map to checklist items
    can_generate = len(errors) == 0
    latest = FinalLogBook.objects.filter(group=group).order_by("-version").first()
    from apps.logbook.serializers import FinalLogBookSerializer

    return Response(
        {
            "success": True,
            "data": {
                "group_id": group.id,
                "group_number": group.group_number,
                "checklist": checklist,
                "can_generate": can_generate,
                "errors": errors,
                "latest": FinalLogBookSerializer(latest).data if latest else None,
                "all_completed": all(checklist.values()) and can_generate,
            },
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def final_logbook_generate(request):
    if request.user.role != "student":
        return Response({"success": False, "message": "Student only"}, status=403)
    group = _get_student_group(request.user)
    if not group:
        return Response({"success": False, "message": "No group"}, status=404)
    from apps.logbook.views import _check_conditions, generate_logbook as _gen_view

    # reuse existing generate logic but call directly
    from django.test import RequestFactory

    # instead manually call service
    from apps.logbook.views import _check_conditions

    errors = _check_conditions(group)
    if errors:
        return Response(
            {"success": False, "message": "Cannot generate logbook", "errors": errors},
            status=403,
        )
    from apps.logbook.services import generate_pdf, PDFGenerationError
    from apps.logbook.models import FinalLogBook

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
        AuditLog.objects.create(
            actor=request.user,
            actor_role=request.user.role,
            action="logbook_generated",
            entity_type="final_logbook",
            entity_id=lb.id,
            new_value={"group": group.id, "version": version},
        )
        from apps.notifications.models import Notification as Notif

        for member in group.members.all():
            Notif.objects.create(
                recipient=member.student,
                notification_type="system",
                title="Logbook generated",
                message=f"Group {group.group_number} logbook v{version} ready",
            )
        from apps.logbook.serializers import FinalLogBookSerializer

        return Response({"success": True, "data": FinalLogBookSerializer(lb).data})
    except PDFGenerationError as e:
        lb.status = "pending"
        lb.remarks = str(e)
        lb.save()
        return Response(
            {"success": False, "message": str(e), "errors": {"pdf": [str(e)]}},
            status=503,
        )
    except Exception as e:
        lb.status = "pending"
        lb.remarks = str(e)
        lb.save()
        return Response({"success": False, "message": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def audit_view(request):
    if request.user.role != "student":
        return Response({"success": False, "message": "Student only"}, status=403)
    group = _get_student_group(request.user)
    if not group:
        return Response({"success": False, "message": "No group"}, status=404)
    # only show audit for own group/submissions/documents
    entity_type = request.query_params.get("entity_type")
    qs = AuditLog.objects.filter(actor=request.user).order_by("-timestamp")[:50]
    # also filter by group-related entities
    # include submission/document/group events where entity_id matches own group
    group_ids = [group.id]
    sub_ids = list(Submission.objects.filter(group=group).values_list("id", flat=True))
    doc_ids = list(Document.objects.filter(group=group).values_list("id", flat=True))
    qs = AuditLog.objects.filter(actor=request.user).order_by("-timestamp")[:100]
    # alternative: show all actor logs for this user
    data = AuditLogSerializer(qs, many=True).data
    return Response({"success": True, "data": data})
