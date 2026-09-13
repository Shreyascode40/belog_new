from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from datetime import timedelta

from apps.groups.models import ProjectGroup, GroupMember
from apps.submissions.models import Submission
from apps.documents.models import Document
from apps.notifications.models import Notification
from apps.audit.models import AuditLog
from apps.reviews.models import Approval, Mark


def _groups_for_user(user):
    if user.role == "student":
        return list(
            ProjectGroup.objects.filter(
                members__student=user, members__status="accepted"
            ).values_list("id", flat=True)
        )
    if user.role == "faculty":
        return list(
            ProjectGroup.objects.filter(
                guide_assignments__faculty=user, guide_assignments__is_active=True
            ).values_list("id", flat=True)
        )
    if user.role == "reviewer":
        return list(
            ProjectGroup.objects.filter(
                reviewer_assignments__faculty=user, reviewer_assignments__is_active=True
            ).values_list("id", flat=True)
        )
    if user.role in ["hod", "admin"]:
        return list(ProjectGroup.objects.all().values_list("id", flat=True))
    return []


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def updates(request):
    since_raw = request.query_params.get("since")
    try:
        since = (
            parse_datetime(since_raw)
            if since_raw
            else timezone.now() - timedelta(seconds=30)
        )
        if since and timezone.is_naive(since):
            since = timezone.make_aware(since)
    except:
        since = timezone.now() - timedelta(seconds=30)
    gids = _groups_for_user(request.user)
    # submissions changed
    subs = (
        Submission.objects.filter(group_id__in=gids, updated_at__gt=since).order_by(
            "-updated_at"
        )[:20]
        if gids
        else []
    )
    docs = (
        Document.objects.filter(group_id__in=gids, updated_at__gt=since).order_by(
            "-updated_at"
        )[:10]
        if gids
        else []
    )
    notes = Notification.objects.filter(
        recipient=request.user, created_at__gt=since
    ).order_by("-created_at")[:20]
    audits = (
        AuditLog.objects.filter(timestamp__gt=since).filter(entity_id__in=gids)[:10]
        if gids
        else []
    )
    # build payload minimal
    data = {
        "server_time": timezone.now().isoformat(),
        "submissions": [
            {
                "id": s.id,
                "group": s.group_id,
                "status": s.status,
                "updated_at": s.updated_at.isoformat(),
                "week": (s.content or {}).get("week"),
            }
            for s in subs
        ],
        "documents": [
            {
                "id": d.id,
                "group": d.group_id,
                "status": d.status,
                "updated_at": d.updated_at.isoformat(),
                "title": d.title,
            }
            for d in docs
        ],
        "notifications": [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat(),
            }
            for n in notes
        ],
        "has_updates": bool(subs or docs or notes),
    }
    resp = Response({"success": True, "data": data})
    resp["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return resp


@api_view(["GET"])
def stream(request):
    from django.http import StreamingHttpResponse
    import json, time
    from django.contrib.auth import get_user_model

    User = get_user_model()
    user = request.user
    if not user or not user.is_authenticated:
        token = request.query_params.get("token") or request.GET.get("token")
        if token:
            try:
                from rest_framework_simplejwt.tokens import AccessToken

                at = AccessToken(token)
                user = User.objects.get(id=at["user_id"])
            except:
                pass
    if not user or not user.is_authenticated:
        return Response({"success": False, "message": "Unauthorized"}, status=401)

    def event_stream():
        gids = _groups_for_user(user)
        yield f"data: {json.dumps({'type': 'connected', 'server_time': timezone.now().isoformat()})}\n\n"
        for _ in range(12):
            time.sleep(5)
            subs = (
                Submission.objects.filter(
                    group_id__in=gids,
                    updated_at__gt=timezone.now() - timedelta(seconds=6),
                ).exists()
                if gids
                else False
            )
            notes = Notification.objects.filter(
                recipient=user,
                created_at__gt=timezone.now() - timedelta(seconds=6),
            ).exists()
            if subs or notes:
                yield f"data: {json.dumps({'type': 'update', 'has_updates': True})}\n\n"
            else:
                yield f": heartbeat\n\n"

    resp = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    resp["Cache-Control"] = "no-cache"
    resp["X-Accel-Buffering"] = "no"
    return resp
