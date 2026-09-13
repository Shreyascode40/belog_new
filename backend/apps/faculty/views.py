from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q

from apps.groups.models import ProjectGroup, GroupMember
from apps.groups.serializers import GroupProfileSerializer
from apps.submissions.models import Submission, SubmissionVersion
from apps.submissions.serializers import (
    SubmissionSerializer,
    SubmissionVersionSerializer,
)
from apps.documents.models import Document, DocumentVersion
from apps.documents.serializers import DocumentSerializer, DocumentVersionSerializer
from apps.reviews.models import Review, ReviewCriterion, Mark, Approval
from apps.reviews.serializers import (
    ReviewSerializer,
    ReviewCriterionSerializer,
    MarkSerializer,
    ApprovalSerializer,
)
from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer
from apps.audit.models import AuditLog, Deadline
from apps.audit.serializers import AuditLogSerializer
from apps.projects.models import ProjectStage, Section
from django.core.exceptions import ValidationError


def _assigned_groups(user, role_hint):
    if not user.is_authenticated:
        return ProjectGroup.objects.none()
    if role_hint == "faculty":
        return ProjectGroup.objects.filter(
            guide_assignments__faculty=user, guide_assignments__is_active=True
        ).distinct()
    if role_hint == "reviewer":
        return ProjectGroup.objects.filter(
            reviewer_assignments__faculty=user, reviewer_assignments__is_active=True
        ).distinct()
    # fallback - union
    return (
        ProjectGroup.objects.filter(
            guide_assignments__faculty=user, guide_assignments__is_active=True
        ).distinct()
        | ProjectGroup.objects.filter(
            reviewer_assignments__faculty=user, reviewer_assignments__is_active=True
        ).distinct()
    ).distinct()


def _can_access_group(user, group, role_hint):
    if user.role in ["hod", "admin"]:
        return True
    qs = _assigned_groups(user, role_hint)
    return qs.filter(id=group.id).exists()


def _require_role(user, allowed):
    if user.role not in allowed:
        raise PermissionDenied(f"Role {user.role} not allowed")


def _dashboard_data(user, role_hint):
    groups = (
        _assigned_groups(user, role_hint)
        if user.role not in ["hod", "admin"]
        else ProjectGroup.objects.all()
    )
    # if hod/admin but requesting faculty/reviewer dashboard, still limit to assigned? we give all for hod visibility but audit says hod broader
    if user.role in ["hod", "admin"] and role_hint in ["faculty", "reviewer"]:
        # hod sees all when hitting faculty endpoint? keep all but not leak via strict check elsewhere
        groups = (
            ProjectGroup.objects.all()
            if role_hint == "faculty"
            else ProjectGroup.objects.all()
        )
        # for precise Faculty distinction we keep assigned only; comment out next line if strict
        # groups=_assigned_groups(user, role_hint) if _assigned_groups(user, role_hint).exists() else ProjectGroup.objects.all()
        pass
    group_ids = list(groups.values_list("id", flat=True))
    subs = Submission.objects.filter(group_id__in=group_ids)
    reviews = Review.objects.filter(group_id__in=group_ids)
    docs = Document.objects.filter(group_id__in=group_ids)
    pending_log = subs.filter(
        status__in=["submitted", "resubmitted", "under_review"]
    ).count()
    pending_reviews = reviews.filter(status__in=["draft", "in_progress"]).count()
    changes_requested = subs.filter(status="changes_required").count()
    approved = subs.filter(status__in=["approved", "locked"]).count()
    completed_reviews = reviews.filter(status="finalized").count()
    upcoming = []
    for dl in Deadline.objects.filter(is_active=True).order_by("due_date")[:5]:
        upcoming.append(
            {
                "stage": dl.stage.name,
                "due_date": dl.due_date,
                "overdue": dl.due_date < timezone.localdate(),
            }
        )
    return {
        "assigned_groups": groups.count(),
        "pending_reviews": pending_reviews,
        "pending_log_entries": pending_log,
        "changes_requested": changes_requested,
        "approved_submissions": approved,
        "completed_reviews": completed_reviews,
        "total_documents": docs.count(),
        "upcoming_deadlines": upcoming,
        "groups": GroupProfileSerializer(groups[:10], many=True).data,
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def faculty_dashboard(request):
    if request.user.role not in ["faculty", "hod", "admin"]:
        return Response({"success": False, "message": "Faculty only"}, status=403)
    data = _dashboard_data(request.user, "faculty")
    return Response({"success": True, "data": data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def reviewer_dashboard(request):
    if request.user.role not in ["reviewer", "hod", "admin"]:
        return Response({"success": False, "message": "Reviewer only"}, status=403)
    data = _dashboard_data(request.user, "reviewer")
    return Response({"success": True, "data": data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def faculty_groups(request):
    if request.user.role not in ["faculty", "hod", "admin"]:
        return Response({"success": False, "message": "Faculty only"}, status=403)
    qs = (
        _assigned_groups(request.user, "faculty")
        if request.user.role == "faculty"
        else ProjectGroup.objects.all()
        if request.user.role in ["hod", "admin"]
        else ProjectGroup.objects.none()
    )
    # allow filtering
    s = request.query_params.get("search")
    if s:
        qs = qs.filter(Q(group_number__icontains=s) | Q(project__title__icontains=s))
    from rest_framework.pagination import PageNumberPagination

    paginator = PageNumberPagination()
    paginator.page_size = 20
    page = paginator.paginate_queryset(qs.order_by("group_number"), request)
    ser = GroupProfileSerializer(page, many=True).data
    # enrich with progress & pending
    for g in ser:
        grp = next((x for x in qs if x.id == g["id"]), None)
        if grp:
            subs = Submission.objects.filter(group_id=g["id"])
            g["pending_action"] = (
                "Review Required"
                if subs.filter(status__in=["submitted", "resubmitted"]).exists()
                else ""
            )
            g["progress_value"] = grp.progress
            g["students_count"] = grp.members.filter(status="accepted").count()
    return paginator.get_paginated_response({"success": True, "data": ser})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def reviewer_groups(request):
    if request.user.role not in ["reviewer", "hod", "admin"]:
        return Response({"success": False, "message": "Reviewer only"}, status=403)
    qs = (
        _assigned_groups(request.user, "reviewer")
        if request.user.role == "reviewer"
        else ProjectGroup.objects.all()
    )
    s = request.query_params.get("search")
    if s:
        qs = qs.filter(Q(group_number__icontains=s) | Q(project__title__icontains=s))
    from rest_framework.pagination import PageNumberPagination

    paginator = PageNumberPagination()
    paginator.page_size = 20
    page = paginator.paginate_queryset(qs.order_by("group_number"), request)
    ser = GroupProfileSerializer(page, many=True).data
    for g in ser:
        grp = next((x for x in qs if x.id == g["id"]), None)
        if grp:
            subs = Submission.objects.filter(group_id=g["id"])
            g["pending_action"] = (
                "Review Required"
                if subs.filter(status__in=["submitted", "resubmitted"]).exists()
                else ""
            )
            g["progress_value"] = grp.progress
    return paginator.get_paginated_response({"success": True, "data": ser})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def group_detail(request, pk, role_hint="faculty"):
    # role_hint is faculty or reviewer
    if role_hint == "faculty" and request.user.role not in ["faculty", "hod", "admin"]:
        return Response({"success": False, "message": "Faculty only"}, status=403)
    if role_hint == "reviewer" and request.user.role not in [
        "reviewer",
        "hod",
        "admin",
    ]:
        return Response({"success": False, "message": "Reviewer only"}, status=403)
    group = get_object_or_404(ProjectGroup, id=pk)
    if not _can_access_group(
        request.user, group, role_hint
    ) and request.user.role not in ["hod", "admin"]:
        raise PermissionDenied("Not assigned to this group")
    data = GroupProfileSerializer(group).data
    # progress detail
    stages = list(
        ProjectStage.objects.filter(academic_year=group.academic_year).order_by("order")
    )
    if not stages:
        stages = list(ProjectStage.objects.all().order_by("order"))
    progress_detail = []
    for st in stages:
        sub = (
            Submission.objects.filter(group=group, section__stage=st)
            .order_by("-created_at")
            .first()
        )
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
        progress_detail.append(
            {
                "id": st.id,
                "name": st.name,
                "order": st.order,
                "slug": st.slug,
                "status": status_val,
                "pct": pct,
                "feedback": sub.review_remarks if sub else "",
            }
        )
    data["progress_detail"] = progress_detail
    data["overall_progress"] = group.progress
    total = len([p for p in progress_detail if p["pct"] == 100])
    data["completed_milestones"] = total
    data["pending_milestones"] = len(
        [p for p in progress_detail if p["pct"] < 100 and p["status"] != "not_started"]
    )
    data["overdue_milestones"] = len(
        [
            p
            for p in progress_detail
            if Deadline.objects.filter(
                stage_id=p["id"],
                academic_year=group.academic_year,
                due_date__lt=timezone.localdate(),
            ).exists()
            and p["pct"] != 100
        ]
    )
    # recent submissions pending
    pending = Submission.objects.filter(
        group=group, status__in=["submitted", "resubmitted", "under_review"]
    ).order_by("-submitted_at")[:5]
    data["pending_reviews"] = SubmissionSerializer(pending, many=True).data
    docs = Document.objects.filter(group=group).order_by("-created_at")[:5]
    data["recent_documents"] = DocumentSerializer(docs, many=True).data
    # recent feedback
    feedbacks = (
        Submission.objects.filter(group=group)
        .exclude(review_remarks="")
        .order_by("-reviewed_at")[:3]
    )
    data["recent_feedback"] = [
        {
            "stage": f.section.stage.name if f.section and f.section.stage else "",
            "remark": f.review_remarks,
            "reviewer": f.reviewed_by.email if f.reviewed_by else "",
        }
        for f in feedbacks
    ]
    AuditLog.objects.create(
        actor=request.user,
        actor_role=request.user.role,
        action="submission_edited",
        entity_type="project_group",
        entity_id=group.id,
        new_value={"viewed": True},
    )
    return Response({"success": True, "data": data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def logbook_list(request, role_hint="faculty"):
    if role_hint == "faculty" and request.user.role not in ["faculty", "hod", "admin"]:
        return Response({"success": False, "message": "Faculty only"}, status=403)
    if role_hint == "reviewer" and request.user.role not in [
        "reviewer",
        "hod",
        "admin",
    ]:
        return Response({"success": False, "message": "Reviewer only"}, status=403)
    qs_groups = (
        _assigned_groups(request.user, role_hint)
        if request.user.role not in ["hod", "admin"]
        else ProjectGroup.objects.all()
    )
    group_ids = list(qs_groups.values_list("id", flat=True))
    qs = (
        Submission.objects.filter(group_id__in=group_ids)
        .select_related("section__stage", "group")
        .order_by("-submitted_at", "-created_at")
    )
    # filters
    gid = request.query_params.get("group")
    week = request.query_params.get("week")
    stage = request.query_params.get("stage")
    status_f = request.query_params.get("status")
    date_f = request.query_params.get("date")
    if gid:
        try:
            gid = int(gid)
            if gid not in group_ids and request.user.role not in ["hod", "admin"]:
                raise PermissionDenied("Group not assigned")
            qs = qs.filter(group_id=gid)
        except ValueError:
            pass
    if week:
        qs = qs.filter(content__week=str(week))  # JSON field contains week
    if stage:
        try:
            qs = qs.filter(section__stage_id=int(stage))
        except:
            qs = qs.filter(section__stage__slug=stage)
    if status_f:
        qs = qs.filter(status=status_f)
    if date_f:
        qs = qs.filter(content__date=date_f)
    from rest_framework.pagination import PageNumberPagination

    paginator = PageNumberPagination()
    paginator.page_size = 20
    page = paginator.paginate_queryset(qs, request)
    data = SubmissionSerializer(page, many=True).data
    for d in data:
        d["group_number"] = next(
            (g.group_number for g in qs_groups if g.id == d["group"]), d["group"]
        )
    return paginator.get_paginated_response({"success": True, "data": data})


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def logbook_review(request, pk, role_hint="faculty"):
    if role_hint == "faculty" and request.user.role not in ["faculty", "hod", "admin"]:
        return Response({"success": False, "message": "Faculty only"}, status=403)
    if role_hint == "reviewer" and request.user.role not in [
        "reviewer",
        "hod",
        "admin",
    ]:
        return Response({"success": False, "message": "Reviewer only"}, status=403)
    # GET returns detail
    sub = get_object_or_404(Submission, id=pk)
    if not _can_access_group(
        request.user, sub.group, role_hint
    ) and request.user.role not in ["hod", "admin"]:
        raise PermissionDenied("Not assigned to this group's submission")
    if request.method == "GET":
        data = SubmissionSerializer(sub).data
        versions = SubmissionVersion.objects.filter(submission=sub).order_by(
            "version_number"
        )
        data["versions"] = SubmissionVersionSerializer(versions, many=True).data
        data["group_detail"] = GroupProfileSerializer(sub.group).data
        AuditLog.objects.create(
            actor=request.user,
            actor_role=request.user.role,
            action="submission_edited",
            entity_type="submission",
            entity_id=sub.id,
            new_value={"viewed": True},
        )
        return Response({"success": True, "data": data})
    # POST review decision
    decision = request.data.get("decision") or request.data.get("status")
    remark = (
        request.data.get("feedback")
        or request.data.get("remark")
        or request.data.get("review_remarks")
        or request.data.get("comment")
        or ""
    )
    # normalize decision
    decision = (decision or "").lower()
    mapping = {
        "approve": "approved",
        "approved": "approved",
        "changes_requested": "changes_required",
        "changes required": "changes_required",
        "changes_required": "changes_required",
        "request_changes": "changes_required",
        "reject": "rejected",
        "rejected": "rejected",
    }
    decision = mapping.get(decision, decision)
    allowed = ["approved", "changes_required", "rejected"]
    if decision not in allowed:
        return Response(
            {
                "success": False,
                "message": "Decision must be APPROVE, CHANGES_REQUESTED or REJECT (if supported)",
                "errors": {"decision": ["Invalid"]},
            },
            status=400,
        )
    # workflow enforcement: cannot approve draft, student cannot approve own etc.
    if sub.status in ["draft"]:
        return Response(
            {
                "success": False,
                "message": "Cannot review a draft submission",
                "errors": {"status": ["Draft cannot be reviewed"]},
            },
            status=400,
        )
    if sub.status in ["approved", "locked"]:
        return Response(
            {
                "success": False,
                "message": "Already approved/locked",
                "errors": {"status": ["Already approved"]},
            },
            status=400,
        )
    if decision == "changes_required" and not remark.strip():
        return Response(
            {
                "success": False,
                "message": "Feedback required for changes requested",
                "errors": {"feedback": ["Required"]},
            },
            status=400,
        )
    # check workflow: only SUBMITTED, RESUBMITTED, UNDER_REVIEW can be decided
    if sub.status not in [
        "submitted",
        "resubmitted",
        "under_review",
        "changes_required",
    ]:
        # still allow but warn
        pass
    # ensure decision allowed per workflow: draft-> cannot, submitted->approved/changes
    # For simplicity allow approved/rejected/changes_required from submitted/resubmitted/under_review
    if decision == "rejected" and sub.status not in [
        "submitted",
        "resubmitted",
        "under_review",
    ]:
        # if workflow doesn't support REJECT, we still allow but keep approval model
        pass
    old_status = sub.status
    if decision == "approved":
        sub.status = "approved"
        sub.reviewed_by = request.user
        sub.reviewed_at = timezone.now()
        sub.review_remarks = remark
        sub.save()
        # create Approval record
        Approval.objects.create(
            submission=sub,
            approver=request.user,
            role=request.user.role,
            decision="approved",
            remark=remark,
        )
        # notify students
        for member in sub.group.members.filter(status="accepted"):
            Notification.objects.create(
                recipient=member.student,
                notification_type="approval",
                title="Log entry approved",
                message=f"{sub.section.stage.name if sub.section and sub.section.stage else 'Log'} approved by {request.user.email}: {remark}",
                related_type="submission",
                related_id=sub.id,
            )
        AuditLog.objects.create(
            actor=request.user,
            actor_role=request.user.role,
            action="submission_approved",
            entity_type="submission",
            entity_id=sub.id,
            previous_value={"status": old_status},
            new_value={"status": "approved", "remark": remark},
        )
    elif decision == "changes_required":
        sub.status = "changes_required"
        sub.review_remarks = remark
        sub.reviewed_by = request.user
        sub.reviewed_at = timezone.now()
        sub.save()
        Approval.objects.create(
            submission=sub,
            approver=request.user,
            role=request.user.role,
            decision="changes_required",
            remark=remark,
        )
        for member in sub.group.members.filter(status="accepted"):
            Notification.objects.create(
                recipient=member.student,
                notification_type="change_request",
                title="Changes requested",
                message=f"{sub.section.stage.name if sub.section and sub.section.stage else 'Log'} — {remark}",
                related_type="submission",
                related_id=sub.id,
            )
        AuditLog.objects.create(
            actor=request.user,
            actor_role=request.user.role,
            action="changes_requested",
            entity_type="submission",
            entity_id=sub.id,
            previous_value={"status": old_status},
            new_value={"status": "changes_required", "remark": remark},
        )
    elif decision == "rejected":
        sub.status = "changes_required"
        sub.review_remarks = remark or "Rejected"
        sub.reviewed_by = request.user
        sub.reviewed_at = timezone.now()
        sub.save()
        Approval.objects.create(
            submission=sub,
            approver=request.user,
            role=request.user.role,
            decision="rejected",
            remark=remark,
        )
        for member in sub.group.members.filter(status="accepted"):
            Notification.objects.create(
                recipient=member.student,
                notification_type="change_request",
                title="Submission rejected",
                message=f"Rejected: {remark}",
                related_type="submission",
                related_id=sub.id,
            )
        AuditLog.objects.create(
            actor=request.user,
            actor_role=request.user.role,
            action="changes_requested",
            entity_type="submission",
            entity_id=sub.id,
            previous_value={"status": old_status},
            new_value={"status": "rejected", "remark": remark},
        )
    return Response({"success": True, "data": SubmissionSerializer(sub).data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def submissions_list(request, role_hint="faculty"):
    return logbook_list(request, role_hint=role_hint)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def documents_list(request, role_hint="faculty"):
    if role_hint == "faculty" and request.user.role not in ["faculty", "hod", "admin"]:
        return Response({"success": False, "message": "Faculty only"}, status=403)
    if role_hint == "reviewer" and request.user.role not in [
        "reviewer",
        "hod",
        "admin",
    ]:
        return Response({"success": False, "message": "Reviewer only"}, status=403)
    qs_groups = (
        _assigned_groups(request.user, role_hint)
        if request.user.role not in ["hod", "admin"]
        else ProjectGroup.objects.all()
    )
    group_ids = list(qs_groups.values_list("id", flat=True))
    if request.method == "GET":
        qs = Document.objects.filter(group_id__in=group_ids).order_by("-created_at")
        gid = request.query_params.get("group")
        if gid:
            try:
                gid = int(gid)
                if gid not in group_ids and request.user.role not in ["hod", "admin"]:
                    raise PermissionDenied("Group not assigned")
                qs = qs.filter(group_id=gid)
            except ValueError:
                pass
        from rest_framework.pagination import PageNumberPagination

        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(qs, request)
        data = DocumentSerializer(page, many=True).data
        # attach versions
        for d in data:
            vers = DocumentVersion.objects.filter(document_id=d["id"]).order_by(
                "version_number"
            )
            from apps.documents.serializers import DocumentVersionSerializer

            d["versions"] = DocumentVersionSerializer(vers, many=True).data
        return paginator.get_paginated_response({"success": True, "data": data})
    return Response(
        {"success": False, "message": "Use student endpoint to upload"}, status=405
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def document_review(request, pk, role_hint="faculty"):
    if role_hint == "faculty" and request.user.role not in ["faculty", "hod", "admin"]:
        return Response({"success": False, "message": "Faculty only"}, status=403)
    if role_hint == "reviewer" and request.user.role not in [
        "reviewer",
        "hod",
        "admin",
    ]:
        return Response({"success": False, "message": "Reviewer only"}, status=403)
    doc = get_object_or_404(Document, id=pk)
    if not _can_access_group(
        request.user, doc.group, role_hint
    ) and request.user.role not in ["hod", "admin"]:
        raise PermissionDenied("Not assigned")
    decision = (
        request.data.get("decision") or request.data.get("status") or ""
    ).lower()
    remark = request.data.get("feedback") or request.data.get("remark") or ""
    if decision not in ["approved", "changes_required", "rejected", "uploaded"]:
        return Response({"success": False, "message": "Decision required"}, status=400)
    old = doc.status
    mapping = {
        "approved": "approved",
        "changes_required": "rejected",
        "rejected": "rejected",
    }
    doc.status = mapping.get(decision, decision)
    doc.remarks = remark
    doc.save()
    AuditLog.objects.create(
        actor=request.user,
        actor_role=request.user.role,
        action="submission_approved" if decision == "approved" else "changes_requested",
        entity_type="document",
        entity_id=doc.id,
        previous_value={"status": old},
        new_value={"status": doc.status, "remark": remark},
    )
    for member in doc.group.members.filter(status="accepted"):
        Notification.objects.create(
            recipient=member.student,
            notification_type="approval"
            if decision == "approved"
            else "change_request",
            title=f"Document {doc.title} {doc.status}",
            message=remark or f"Document reviewed: {doc.status}",
            related_type="document",
            related_id=doc.id,
        )
    return Response({"success": True, "data": DocumentSerializer(doc).data})


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def evaluations(request, role_hint="faculty"):
    if role_hint == "faculty" and request.user.role not in ["faculty", "hod", "admin"]:
        return Response({"success": False, "message": "Faculty only"}, status=403)
    if role_hint == "reviewer" and request.user.role not in [
        "reviewer",
        "hod",
        "admin",
    ]:
        return Response({"success": False, "message": "Reviewer only"}, status=403)
    qs_groups = (
        _assigned_groups(request.user, role_hint)
        if request.user.role not in ["hod", "admin"]
        else ProjectGroup.objects.all()
    )
    group_ids = list(qs_groups.values_list("id", flat=True))
    if request.method == "GET":
        gid = request.query_params.get("group")
        qs = Review.objects.filter(group_id__in=group_ids)
        if gid:
            try:
                qs = qs.filter(group_id=int(gid))
            except:
                pass
        data = ReviewSerializer(qs.order_by("review_number"), many=True).data
        # enrich with criteria
        for r in data:
            crits = ReviewCriterion.objects.filter(review_id=r["id"])
            r["criteria"] = ReviewCriterionSerializer(crits, many=True).data
            marks = Mark.objects.filter(
                group_id=r["group"], criterion__review_id=r["id"]
            )
            r["marks"] = MarkSerializer(marks, many=True).data
        return Response({"success": True, "data": data})
    # POST - create/update mark
    # expected: criterion, group, obtained_marks, remarks
    criterion_id = request.data.get("criterion") or request.data.get("criterion_id")
    group_id = request.data.get("group") or request.data.get("group_id")
    obtained = request.data.get("obtained_marks")
    remarks = request.data.get("remarks") or request.data.get("remark") or ""
    if not criterion_id or not group_id or obtained is None:
        return Response(
            {
                "success": False,
                "message": "criterion, group, obtained_marks required",
                "errors": {"fields": ["required"]},
            },
            status=400,
        )
    try:
        criterion = ReviewCriterion.objects.get(id=criterion_id)
        group = ProjectGroup.objects.get(id=group_id)
    except (ReviewCriterion.DoesNotExist, ProjectGroup.DoesNotExist):
        return Response(
            {"success": False, "message": "Invalid criterion or group"}, status=400
        )
    if group.id not in group_ids and request.user.role not in ["hod", "admin"]:
        raise PermissionDenied("Group not assigned")
    # check authorization: reviewer must be assigned to that group+review
    # we allow faculty who is guide for that group
    try:
        obtained_val = float(obtained)
    except:
        return Response(
            {
                "success": False,
                "message": "Invalid marks",
                "errors": {"obtained_marks": ["must be number"]},
            },
            status=400,
        )
    if obtained_val < 0:
        return Response(
            {
                "success": False,
                "message": "Marks cannot be negative",
                "errors": {"obtained_marks": ["negative"]},
            },
            status=400,
        )
    if obtained_val > float(criterion.max_marks):
        return Response(
            {
                "success": False,
                "message": f"Marks cannot exceed maximum {criterion.max_marks}",
                "errors": {"obtained_marks": [f"max {criterion.max_marks}"]},
            },
            status=400,
        )
    # check if finalized
    existing = Mark.objects.filter(
        criterion=criterion, group=group, reviewer=request.user
    ).first()
    if existing and existing.is_finalized:
        return Response(
            {
                "success": False,
                "message": "Evaluation locked/finalized — cannot modify except via correction workflow",
                "errors": {"mark": ["finalized"]},
            },
            status=403,
        )
    # check if review is finalized
    rev = criterion.review
    if rev.status == "finalized":
        return Response(
            {
                "success": False,
                "message": "Review already finalized",
                "errors": {"review": ["finalized"]},
            },
            status=403,
        )
    if existing:
        existing.obtained_marks = obtained_val
        existing.remarks = remarks
        existing.save()
        mark = existing
    else:
        mark = Mark.objects.create(
            criterion=criterion,
            group=group,
            reviewer=request.user,
            obtained_marks=obtained_val,
            remarks=remarks,
            status="saved",
        )
    AuditLog.objects.create(
        actor=request.user,
        actor_role=request.user.role,
        action="marks_entered",
        entity_type="mark",
        entity_id=mark.id,
        new_value={
            "group": group.id,
            "criterion": criterion.id,
            "marks": str(obtained_val),
        },
    )
    return Response({"success": True, "data": MarkSerializer(mark).data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def finalize_evaluation(request, pk, role_hint="faculty"):
    if role_hint == "faculty" and request.user.role not in ["faculty", "hod", "admin"]:
        return Response({"success": False, "message": "Faculty only"}, status=403)
    if role_hint == "reviewer" and request.user.role not in [
        "reviewer",
        "hod",
        "admin",
    ]:
        return Response({"success": False, "message": "Reviewer only"}, status=403)
    review = get_object_or_404(Review, id=pk)
    if not _can_access_group(
        request.user, review.group, role_hint
    ) and request.user.role not in ["hod", "admin"]:
        raise PermissionDenied("Not assigned")
    if review.criteria.count() == 0:
        return Response({"success": False, "message": "No criteria"}, status=400)
    # ensure all marks exist
    missing = []
    for crit in review.criteria.all():
        if not Mark.objects.filter(criterion=crit, group=review.group).exists():
            missing.append(crit.name)
    if missing:
        return Response(
            {"success": False, "message": f"Missing marks for: {', '.join(missing)}"},
            status=400,
        )
    review.status = "finalized"
    review.finalized_at = timezone.now()
    review.finalized_by = request.user
    # compute totals
    marks = Mark.objects.filter(criterion__review=review, group=review.group)
    total_obt = sum(float(m.obtained_marks) for m in marks)
    total_max = sum(float(c.max_marks) for c in review.criteria.all())
    review.total_obtained_marks = total_obt
    review.total_max_marks = total_max
    review.save()
    for m in marks:
        m.is_finalized = True
        m.status = "finalized"
        m.finalized_at = timezone.now()
        m.finalized_by = request.user
        m.save()
    AuditLog.objects.create(
        actor=request.user,
        actor_role=request.user.role,
        action="marks_finalized",
        entity_type="review",
        entity_id=review.id,
        new_value={"total": str(total_obt)},
    )
    return Response({"success": True, "data": ReviewSerializer(review).data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def history(request, role_hint="faculty"):
    if role_hint == "faculty" and request.user.role not in ["faculty", "hod", "admin"]:
        return Response({"success": False, "message": "Faculty only"}, status=403)
    if role_hint == "reviewer" and request.user.role not in [
        "reviewer",
        "hod",
        "admin",
    ]:
        return Response({"success": False, "message": "Reviewer only"}, status=403)
    qs_groups = (
        _assigned_groups(request.user, role_hint)
        if request.user.role not in ["hod", "admin"]
        else ProjectGroup.objects.all()
    )
    group_ids = list(qs_groups.values_list("id", flat=True))
    qs = (
        Approval.objects.filter(submission__group_id__in=group_ids)
        .select_related("submission__group", "approver")
        .order_by("-decided_at")
    )
    gid = request.query_params.get("group")
    if gid:
        try:
            qs = qs.filter(submission__group_id=int(gid))
        except:
            pass
    stage = request.query_params.get("stage")
    if stage:
        try:
            qs = qs.filter(submission__section__stage_id=int(stage))
        except:
            qs = qs.filter(submission__section__stage__slug=stage)
    status_f = request.query_params.get("status")
    if status_f:
        qs = qs.filter(decision=status_f)
    from rest_framework.pagination import PageNumberPagination

    paginator = PageNumberPagination()
    paginator.page_size = 20
    page = paginator.paginate_queryset(qs, request)
    data = ApprovalSerializer(page, many=True).data
    return paginator.get_paginated_response({"success": True, "data": data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def notifications(request, role_hint="faculty"):
    if role_hint == "faculty" and request.user.role not in ["faculty", "hod", "admin"]:
        return Response({"success": False, "message": "Faculty only"}, status=403)
    if role_hint == "reviewer" and request.user.role not in [
        "reviewer",
        "hod",
        "admin",
    ]:
        return Response({"success": False, "message": "Reviewer only"}, status=403)
    qs = Notification.objects.filter(recipient=request.user).order_by("-created_at")
    is_read = request.query_params.get("is_read")
    if is_read in ["true", "false"]:
        qs = qs.filter(is_read=(is_read == "true"))
    from rest_framework.pagination import PageNumberPagination

    paginator = PageNumberPagination()
    paginator.page_size = 20
    page = paginator.paginate_queryset(qs, request)
    data = NotificationSerializer(page, many=True).data
    return paginator.get_paginated_response(
        {
            "success": True,
            "data": data,
            "unread_count": Notification.objects.filter(
                recipient=request.user, is_read=False
            ).count(),
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def notification_read(request, pk, role_hint="faculty"):
    n = get_object_or_404(Notification, id=pk, recipient=request.user)
    n.is_read = True
    n.read_at = timezone.now()
    n.save()
    return Response({"success": True, "data": NotificationSerializer(n).data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def notifications_mark_all(request, role_hint="faculty"):
    if request.user.role not in ["faculty", "reviewer", "hod", "admin"]:
        return Response({"success": False, "message": "Not allowed"}, status=403)
    Notification.objects.filter(recipient=request.user, is_read=False).update(
        is_read=True, read_at=timezone.now()
    )
    return Response({"success": True})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def audit_trail(request, role_hint="faculty"):
    if role_hint == "faculty" and request.user.role not in ["faculty", "hod", "admin"]:
        return Response({"success": False, "message": "Faculty only"}, status=403)
    if role_hint == "reviewer" and request.user.role not in [
        "reviewer",
        "hod",
        "admin",
    ]:
        return Response({"success": False, "message": "Reviewer only"}, status=403)
    qs_groups = (
        _assigned_groups(request.user, role_hint)
        if request.user.role not in ["hod", "admin"]
        else ProjectGroup.objects.all()
    )
    group_ids = list(qs_groups.values_list("id", flat=True))
    # show audit for actor=self or entity_type groups/submissions related to assigned groups
    qs = AuditLog.objects.filter(
        Q(actor=request.user)
        | Q(
            entity_type="submission",
            entity_id__in=Submission.objects.filter(group_id__in=group_ids).values_list(
                "id", flat=True
            ),
        )
        | Q(
            entity_type="document",
            entity_id__in=Document.objects.filter(group_id__in=group_ids).values_list(
                "id", flat=True
            ),
        )
        | Q(entity_type="project_group", entity_id__in=group_ids)
    ).order_by("-timestamp")[:100]
    data = AuditLogSerializer(qs, many=True).data
    return Response({"success": True, "data": data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def progress(request, role_hint="faculty"):
    if role_hint == "faculty" and request.user.role not in ["faculty", "hod", "admin"]:
        return Response({"success": False, "message": "Faculty only"}, status=403)
    if role_hint == "reviewer" and request.user.role not in [
        "reviewer",
        "hod",
        "admin",
    ]:
        return Response({"success": False, "message": "Reviewer only"}, status=403)
    qs_groups = (
        _assigned_groups(request.user, role_hint)
        if request.user.role not in ["hod", "admin"]
        else ProjectGroup.objects.all()
    )
    group_ids = list(qs_groups.values_list("id", flat=True))
    # if group_id param given, return per-group progress else aggregate?
    gid = request.query_params.get("group")
    if gid:
        try:
            group = ProjectGroup.objects.get(id=int(gid))
            if not _can_access_group(
                request.user, group, role_hint
            ) and request.user.role not in ["hod", "admin"]:
                raise PermissionDenied("Not assigned")
            stages = list(
                ProjectStage.objects.filter(academic_year=group.academic_year).order_by(
                    "order"
                )
            )
            result = []
            for st in stages:
                sub = (
                    Submission.objects.filter(group=group, section__stage=st)
                    .order_by("-created_at")
                    .first()
                )
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
                result.append(
                    {
                        "id": st.id,
                        "name": st.name,
                        "order": st.order,
                        "status": status_val,
                        "pct": pct,
                        "feedback": sub.review_remarks if sub else "",
                    }
                )
            return Response(
                {
                    "success": True,
                    "data": {
                        "group": group.group_number,
                        "overall": group.progress,
                        "stages": result,
                    },
                }
            )
        except ProjectGroup.DoesNotExist:
            return Response(
                {"success": False, "message": "Group not found"}, status=404
            )
    # aggregate all groups progress summary
    summary = []
    for g in qs_groups[:20]:
        summary.append(
            {
                "group_id": g.id,
                "group_number": g.group_number,
                "project": g.project.title if g.project else "",
                "progress": g.progress,
            }
        )
    return Response({"success": True, "data": summary})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def deadlines(request, role_hint="faculty"):
    if role_hint == "faculty" and request.user.role not in ["faculty", "hod", "admin"]:
        return Response({"success": False, "message": "Faculty only"}, status=403)
    if role_hint == "reviewer" and request.user.role not in [
        "reviewer",
        "hod",
        "admin",
    ]:
        return Response({"success": False, "message": "Reviewer only"}, status=403)
    qs_groups = (
        _assigned_groups(request.user, role_hint)
        if request.user.role not in ["hod", "admin"]
        else ProjectGroup.objects.all()
    )
    # deadlines for academic years of assigned groups
    ay_ids = list(qs_groups.values_list("academic_year_id", flat=True).distinct())
    qs = Deadline.objects.filter(academic_year_id__in=ay_ids, is_active=True).order_by(
        "due_date"
    )
    # annotate overdue
    data = []
    for dl in qs[:20]:
        data.append(
            {
                "stage": dl.stage.name,
                "stage_order": dl.stage.order,
                "due_date": dl.due_date,
                "start_date": dl.start_date,
                "overdue": dl.due_date < timezone.localdate(),
                "due_today": dl.due_date == timezone.localdate(),
            }
        )
    submissions = Submission.objects.filter(
        group_id__in=qs_groups.values_list("id", flat=True),
        status__in=["submitted", "resubmitted"],
    ).order_by("-submitted_at")[:5]
    pending = [
        {
            "group_number": s.group.group_number,
            "stage": s.section.stage.name if s.section and s.section.stage else "",
            "submitted_at": s.submitted_at,
        }
        for s in submissions
    ]
    return Response(
        {"success": True, "data": {"deadlines": data, "pending_submissions": pending}}
    )
