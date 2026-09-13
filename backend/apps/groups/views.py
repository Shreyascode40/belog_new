from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.conf import settings
from django.utils import timezone
from .models import (
    ProjectGroup,
    GroupMember,
    ProjectGuideAssignment,
    ReviewerAssignment,
)
from .serializers import (
    ProjectGroupSerializer,
    GroupMemberSerializer,
    GuideAssignmentSerializer,
    ReviewerAssignmentSerializer,
    GroupProfileSerializer,
)

GROUP_MIN_SIZE = int(getattr(settings, "GROUP_MIN_SIZE", 4))
GROUP_MAX_SIZE = int(getattr(settings, "GROUP_MAX_SIZE", 4))


def _is_group_member(user, group):
    return group.members.filter(
        student=user, status="accepted", is_active=True
    ).exists()


def _can_edit_group(user, group):
    if user.role in ["hod", "admin"]:
        return False
    if user.role == "student" and _is_group_member(user, group):
        if getattr(group, "is_locked", False):
            return False
        return True
    return False


class ProjectGroupViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectGroupSerializer

    def get_queryset(self):
        qs = (
            ProjectGroup.objects.select_related(
                "academic_year", "department", "project", "updated_by"
            )
            .prefetch_related(
                "members__student__student_profile",
                "guide_assignments__faculty__faculty_profile",
            )
            .all()
        )
        u = self.request.user
        if u and u.is_authenticated and u.role == "student":
            return qs.filter(members__student=u, members__status="accepted").distinct()
        if u and u.role in ["faculty", "reviewer"]:
            return (
                qs.filter(guide_assignments__faculty=u).distinct()
                | qs.filter(reviewer_assignments__faculty=u).distinct()
                | qs.filter(members__student=u, members__status="accepted").distinct()
            )
        return qs

    def get_serializer_class(self):
        if self.action in ["my_profile", "profile"]:
            return GroupProfileSerializer
        return ProjectGroupSerializer

    @action(detail=False, methods=["get"], url_path="config")
    def config(self, request):
        return Response(
            {
                "success": True,
                "data": {
                    "group_min_size": GROUP_MIN_SIZE,
                    "group_max_size": GROUP_MAX_SIZE,
                },
            }
        )

    @action(detail=False, methods=["get"], url_path="my-profile")
    def my_profile(self, request, pk=None):
        group = self.get_queryset().first()
        if not group:
            gid = request.query_params.get("group_id")
            if gid and request.user.role in ["hod", "admin", "faculty", "reviewer"]:
                try:
                    group = (
                        ProjectGroup.objects.select_related(
                            "academic_year", "department", "project", "updated_by"
                        )
                        .prefetch_related(
                            "members__student__student_profile",
                            "guide_assignments__faculty__faculty_profile",
                        )
                        .get(id=gid)
                    )
                except ProjectGroup.DoesNotExist:
                    return Response(
                        {"success": False, "message": "Group not found"}, status=404
                    )
        if not group:
            return Response(
                {
                    "success": True,
                    "data": None,
                    "message": "No group found — create one via Cover Page",
                }
            )
        can_edit = _can_edit_group(request.user, group)
        data = GroupProfileSerializer(group).data
        data["can_edit"] = can_edit
        data["is_locked"] = group.is_locked
        return Response({"success": True, "data": data})

    @action(detail=True, methods=["get", "put", "patch"], url_path="profile")
    def profile(self, request, pk=None):
        group = self.get_object()
        if request.method == "GET":
            data = GroupProfileSerializer(group).data
            data["can_edit"] = _can_edit_group(request.user, group)
            data["is_locked"] = group.is_locked
            return Response({"success": True, "data": data})
        if not _can_edit_group(request.user, group):
            if group.is_locked:
                return Response(
                    {
                        "success": False,
                        "message": "Group is locked — submitted/approved, no edits allowed",
                    },
                    status=423,
                )
            return Response(
                {"success": False, "message": "Only members of this group can edit"},
                status=403,
            )
        data = request.data
        errors = {}
        project_fields = {}
        if "project_title" in data or "title" in data:
            project_fields["title"] = (
                data.get("project_title") or data.get("title") or ""
            ).strip()
            if not project_fields["title"]:
                errors["project_title"] = ["Project Title is required"]
            elif len(project_fields["title"]) < 5:
                errors["project_title"] = ["Title must be at least 5 characters"]
        if "area_domain" in data or "area" in data:
            project_fields["area_domain"] = (
                data.get("area_domain") or data.get("area") or ""
            ).strip()
            if not project_fields["area_domain"]:
                errors["area_domain"] = ["Project Domain/Area is required"]
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
        from apps.audit.models import AuditLog

        prev = {}
        if group.project:
            prev = {
                "title": group.project.title,
                "area_domain": group.project.area_domain,
                "description": group.project.description,
            }
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
        old_updated = group.updated_at
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
        return Response(
            {"success": True, "data": data_out, "message": "Group profile updated"}
        )

    def perform_update(self, serializer):
        group = serializer.instance if hasattr(serializer, "instance") else None
        if group and not _can_edit_group(self.request.user, group):
            if getattr(group, "is_locked", False):
                raise PermissionDenied(
                    {
                        "message": "Group is locked — no edits allowed",
                        "errors": {"locked": ["Submitted/locked by authority"]},
                    }
                )
            raise PermissionDenied({"message": "Only members of this group can edit"})
        serializer.save(updated_by=self.request.user)

    def perform_create(self, serializer):
        user = self.request.user
        data = self.request.data
        from apps.academics.models import AcademicYear, Department

        ay_id = data.get("academic_year") or data.get("academic_year_id")
        dept_id = data.get("department") or data.get("department_id")
        if ay_id:
            ay = AcademicYear.objects.get(id=ay_id)
        else:
            ay = (
                AcademicYear.objects.filter(is_current=True).first()
                or AcademicYear.objects.first()
            )
        if dept_id:
            dept = Department.objects.get(id=dept_id)
        else:
            dept = (
                Department.objects.filter(code="COMP").first()
                or Department.objects.first()
            )
        if not dept:
            dept, _ = Department.objects.get_or_create(
                code="COMP", defaults={"name": "Computer Engineering"}
            )
        if not ay:
            from datetime import date

            ay, _ = AcademicYear.objects.get_or_create(
                year_label="2024-25",
                defaults={
                    "start_date": date(2024, 7, 1),
                    "end_date": date(2025, 6, 30),
                    "department": dept,
                    "is_current": True,
                },
            )
        if user.role not in ["student"]:
            raise PermissionDenied(
                {
                    "message": "Only students can create groups via Cover Page",
                    "errors": {"role": ["HOD/Faculty cannot create student groups"]},
                }
            )
        if GroupMember.objects.filter(
            student=user,
            group__academic_year=ay,
            group__is_active=True,
            status="accepted",
        ).exists():
            raise ValidationError(
                {"group": ["You are already active in a group for this academic year"]}
            )
        existing = ProjectGroup.objects.filter(
            academic_year=ay, department=dept
        ).order_by("-group_number")
        max_num = 0
        for g in existing:
            try:
                max_num = max(max_num, int(g.group_number))
            except Exception:
                pass
        group_number = str(max_num + 1).zfill(2)
        from apps.projects.models import Project

        project_title = data.get("project_title") or data.get("title") or "Untitled"
        area = data.get("area") or data.get("area_domain") or ""
        project = Project.objects.create(
            title=project_title,
            area_domain=area,
            description=data.get("description", ""),
            academic_year=ay,
            created_by=user,
        )
        group = serializer.save(
            academic_year=ay,
            department=dept,
            group_number=group_number,
            project=project,
            updated_by=user,
        )
        from apps.accounts.models import StudentProfile

        prof, _ = StudentProfile.objects.get_or_create(
            user=user,
            defaults={
                "roll_number": f"4100{user.id:04d}",
                "name": f"{user.first_name} {user.last_name}".strip() or user.username,
                "email": user.email,
                "department": dept.name if dept else "Computer Engineering",
                "academic_year": ay,
            },
        )
        GroupMember.objects.create(
            group=group,
            student=user,
            role="leader",
            status="accepted",
            acknowledged=False,
            te_result=prof.roll_number or "",
            contribution="",
        )
        invites = (
            data.get("invites")
            or data.get("member_emails")
            or data.get("members")
            or []
        )
        if isinstance(invites, str):
            import json

            try:
                invites = json.loads(invites)
            except Exception:
                invites = [invites]
        for inv in invites[: GROUP_MAX_SIZE - 1]:
            email = inv.get("email") if isinstance(inv, dict) else inv
            roll = inv.get("roll_number") if isinstance(inv, dict) else None
            te = inv.get("te_result", "") if isinstance(inv, dict) else ""
            contrib = inv.get("contribution", "") if isinstance(inv, dict) else ""
            from django.contrib.auth import get_user_model

            User = get_user_model()
            target = None
            if email:
                target = User.objects.filter(email=email).first()
            if not target and roll:
                from apps.accounts.models import StudentProfile

                prof2 = StudentProfile.objects.filter(roll_number=roll).first()
                if prof2:
                    target = prof2.user
            if target:
                if GroupMember.objects.filter(
                    student=target,
                    group__academic_year=ay,
                    group__is_active=True,
                    status="accepted",
                ).exists():
                    continue
                try:
                    tprof = target.student_profile
                    te = te or tprof.roll_number or ""
                except Exception:
                    StudentProfile.objects.get_or_create(
                        user=target,
                        defaults={
                            "roll_number": f"4100{target.id:04d}",
                            "name": target.username,
                            "email": target.email,
                            "department": dept.name if dept else "Computer Engineering",
                            "academic_year": ay,
                        },
                    )
                GroupMember.objects.create(
                    group=group,
                    student=target,
                    role="member",
                    status="invited",
                    te_result=te,
                    contribution=contrib,
                )
        from apps.audit.models import AuditLog

        AuditLog.objects.create(
            actor=user,
            actor_role=user.role,
            action="group_created",
            entity_type="project_group",
            entity_id=group.id,
            new_value={"group_number": group_number, "project_title": project_title},
        )
        return group

    @action(detail=True, methods=["post"], url_path="add-member-direct")
    def add_member_direct(self, request, pk=None):
        g = self.get_object()
        if not _can_edit_group(request.user, g):
            return Response(
                {
                    "success": False,
                    "message": "Only group members can add members or group is locked",
                },
                status=403,
            )
        data = request.data
        if (
            g.members.filter(status="accepted", is_active=True).count()
            >= GROUP_MAX_SIZE
        ):
            return Response(
                {
                    "success": False,
                    "message": f"Group size exceeds max {GROUP_MAX_SIZE}",
                },
                status=400,
            )
        email = (data.get("email") or "").strip().lower()
        name = (data.get("name") or "").strip()
        roll = (data.get("roll_number") or data.get("prn") or "").strip()
        if not email or not name or not roll:
            return Response(
                {
                    "success": False,
                    "message": "Name, PRN/Roll Number and Email are required",
                    "errors": {
                        "name": ["Required"],
                        "roll_number": ["Required"],
                        "email": ["Required"],
                    },
                },
                status=400,
            )
        from django.contrib.auth import get_user_model
        from apps.accounts.models import StudentProfile

        User = get_user_model()
        user, created = User.objects.get_or_create(
            email=email, defaults={"username": email.split("@")[0], "role": "student"}
        )
        if created:
            user.set_password("pass1234")
            user.save()
        try:
            prof, _ = StudentProfile.objects.get_or_create(
                user=user,
                defaults={
                    "name": name,
                    "roll_number": roll,
                    "mobile": data.get("mobile", ""),
                    "exam_seat_number": data.get("exam_seat_number", ""),
                    "email": email,
                    "department": g.department.name
                    if g.department
                    else "Computer Engineering",
                    "academic_year": g.academic_year,
                },
            )
        except Exception as e:
            if "UNIQUE constraint failed" in str(e) and "roll_number" in str(e):
                return Response(
                    {
                        "success": False,
                        "message": f"Roll number {roll} already exists — use a unique PRN",
                        "errors": {"roll_number": ["Already exists"]},
                    },
                    status=400,
                )
            return Response({"success": False, "message": str(e)}, status=400)
        for field in ["name", "roll_number", "mobile", "exam_seat_number", "email"]:
            if data.get(field):
                setattr(prof, field, data.get(field) if field != "email" else email)
        if data.get("prn") and not data.get("roll_number"):
            prof.roll_number = data.get("prn")
        try:
            prof.save()
        except Exception as e:
            if "UNIQUE constraint failed" in str(e) and "roll_number" in str(e):
                return Response(
                    {
                        "success": False,
                        "message": f"Roll number {roll} already exists",
                        "errors": {"roll_number": ["Already exists"]},
                    },
                    status=400,
                )
            if "UNIQUE constraint failed" in str(e) and "email" in str(e):
                return Response(
                    {
                        "success": False,
                        "message": f"Email {email} already exists",
                        "errors": {"email": ["Already exists"]},
                    },
                    status=400,
                )
            return Response({"success": False, "message": str(e)}, status=400)
        if GroupMember.objects.filter(student=user, group=g).exists():
            return Response(
                {"success": False, "message": "Already a member"}, status=400
            )
        if (
            GroupMember.objects.filter(
                student=user,
                group__academic_year=g.academic_year,
                group__is_active=True,
                status="accepted",
            )
            .exclude(group=g)
            .exists()
        ):
            return Response(
                {
                    "success": False,
                    "message": "Already in another active group this academic year",
                },
                status=400,
            )
        role = data.get("role", "member")
        if role not in ["leader", "member"]:
            role = "member"
        if g.members.filter(role="leader").exists() and role == "leader":
            role = "member"
        member = GroupMember.objects.create(
            group=g,
            student=user,
            role=role,
            status="accepted",
            te_result=data.get("te_result", ""),
            contribution=data.get("contribution", ""),
        )
        g.updated_by = request.user
        g.save(update_fields=["updated_at", "updated_by"])
        from apps.audit.models import AuditLog

        AuditLog.objects.create(
            actor=request.user,
            actor_role=request.user.role,
            action="student_added",
            entity_type="group_member",
            entity_id=member.id,
            new_value={"email": email, "roll": roll},
        )
        return Response(
            {"success": True, "data": GroupMemberSerializer(member).data}, status=201
        )

    @action(detail=True, methods=["post"], url_path="add-member")
    def add_member(self, request, pk=None):
        g = self.get_object()
        if not _can_edit_group(request.user, g):
            return Response(
                {"success": False, "message": "Not allowed or locked"}, status=403
            )
        data = {**request.data, "group": g.id, "status": "invited"}
        s = GroupMemberSerializer(data=data)
        s.is_valid(raise_exception=True)
        student_id = request.data.get("student")
        if (
            GroupMember.objects.filter(
                student_id=student_id,
                group__academic_year=g.academic_year,
                group__is_active=True,
                status="accepted",
            )
            .exclude(group=g)
            .exists()
        ):
            return Response(
                {
                    "success": False,
                    "message": "Student already in another active group this academic year",
                },
                status=400,
            )
        if (
            g.members.filter(status="accepted", is_active=True).count()
            >= GROUP_MAX_SIZE
        ):
            return Response(
                {
                    "success": False,
                    "message": f"Group size exceeds max {GROUP_MAX_SIZE}",
                },
                status=400,
            )
        obj = s.save()
        try:
            prof = obj.student.student_profile
            updated = False
            if not obj.te_result and getattr(prof, "roll_number", ""):
                obj.te_result = prof.roll_number
                updated = True
            if updated:
                obj.save()
        except Exception:
            from apps.accounts.models import StudentProfile

            StudentProfile.objects.get_or_create(
                user=obj.student,
                defaults={
                    "roll_number": f"4100{obj.student.id:04d}",
                    "name": obj.student.username,
                    "email": obj.student.email,
                },
            )
        return Response(GroupMemberSerializer(obj).data, status=201)

    @action(detail=True, methods=["post"], url_path="seed-student")
    def seed_student(self, request, pk=None):
        g = self.get_object()
        u = request.user
        if u.role == "student" and not g.members.filter(student=u).exists():
            return Response({"success": False, "message": "Not your group"}, status=403)
        from apps.projects.models import ProjectStage, Section
        from apps.submissions.models import Submission
        from apps.accounts.models import StudentProfile

        for m in g.members.all():
            prof, _ = StudentProfile.objects.get_or_create(
                user=m.student,
                defaults={"roll_number": f"4100{m.id}", "name": m.student.username},
            )
            prof.name = prof.name or m.student.username
            prof.mobile = prof.mobile or "9876543210"
            prof.exam_seat_number = prof.exam_seat_number or f"SEAT{prof.roll_number}"
            prof.email = prof.email or m.student.email
            prof.department = prof.department or "Computer Engineering"
            prof.save()
        sample = {
            "project-info": {
                "title": g.project.title if g.project else "AI Based Logbook System",
                "area": g.project.area_domain if g.project else "AI/ML",
                "description": "Sample project auto-filled from student side",
            },
            "group-info": {"group_no": g.group_number, "members": g.members.count()},
            "student-info": {"filled": True},
            "schedule": {"sem1": "June-Nov", "sem2": "Dec-May"},
            "topic": {
                "topic1": g.project.title if g.project else "Topic 1",
                "topic2": "Alternative Topic",
            },
            "activities": {
                "June": "Group Submission, Guide Allocation, Domain Finalization"
            },
            "review-1": {
                "problem": "Automate logbook",
                "objectives": "Digitize workflow",
            },
            "req-analysis": {"requirements": "RTM with 10 reqs"},
            "design": {"uml": "Class, Sequence, DFD"},
            "review-2": {"feasibility": "Feasible"},
            "development": {"stack": "Django+React", "modules": "Auth, Workflow, PDF"},
            "testing": {"cases": "Unit, API, Security"},
            "review-3": {"final": "Ready"},
            "competition": {"events": "Smart India Hackathon"},
            "term": {"checklist": "Term-I/II done"},
            "final-sub": {"ready": True},
            "final-verify": {"verified": True},
            "logbook": {"generate": True},
        }
        created = 0
        for stage in ProjectStage.objects.filter(
            academic_year=g.academic_year
        ).order_by("order"):
            content = sample.get(
                stage.slug,
                {
                    "info": f"Sample data for {stage.name}",
                    "filled_by": u.email,
                    "at": timezone.now().isoformat(),
                },
            )
            sec, _ = Section.objects.get_or_create(
                group=g,
                stage=stage,
                section_type=stage.slug,
                defaults={
                    "title": stage.name,
                    "owner_role": "student",
                    "content": content,
                    "status": "draft",
                },
            )
            sec.content = content
            sec.status = "draft"
            sec.save()
            sub, _ = Submission.objects.get_or_create(
                section=sec,
                group=g,
                submitted_by=u,
                defaults={"content": content, "status": "draft", "version": 1},
            )
            sub.content = content
            sub.status = "draft"
            sub.save()
            created += 1
        return Response(
            {
                "success": True,
                "message": f"Seeded {created} stages for Group {g.group_number}",
                "data": {"stages": created},
            }
        )

    @action(detail=True, methods=["post"], url_path="accept-invite")
    def accept_invite(self, request, pk=None):
        from django.shortcuts import get_object_or_404

        g = get_object_or_404(ProjectGroup, id=pk)
        m = g.members.filter(student=request.user, status="invited").first()
        if not m:
            return Response(
                {"success": False, "message": "No pending invite"}, status=404
            )
        if (
            GroupMember.objects.filter(
                student=request.user,
                group__academic_year=g.academic_year,
                group__is_active=True,
                status="accepted",
            )
            .exclude(group=g)
            .exists()
        ):
            return Response(
                {
                    "success": False,
                    "message": "Already in another active group this academic year",
                },
                status=400,
            )
        m.status = "accepted"
        m.is_active = True
        m.save()
        return Response({"success": True, "data": GroupMemberSerializer(m).data})

    @action(detail=True, methods=["post"], url_path="decline-invite")
    def decline_invite(self, request, pk=None):
        from django.shortcuts import get_object_or_404

        g = get_object_or_404(ProjectGroup, id=pk)
        m = g.members.filter(student=request.user, status="invited").first()
        if not m:
            return Response(
                {"success": False, "message": "No pending invite"}, status=404
            )
        m.status = "declined"
        m.is_active = False
        m.save()
        return Response({"success": True})

    @action(detail=True, methods=["post"], url_path="acknowledge")
    def acknowledge(self, request, pk=None):
        g = self.get_object()
        m = g.members.filter(student=request.user).first()
        if not m:
            return Response({"success": False, "message": "Not a member"}, status=403)
        m.acknowledged = True
        m.acknowledged_at = timezone.now()
        if "contribution" in request.data:
            m.contribution = request.data["contribution"]
        if "te_result" in request.data:
            m.te_result = request.data["te_result"]
        m.save()
        return Response({"success": True, "data": GroupMemberSerializer(m).data})

    @action(detail=True, methods=["post"], url_path="submit-information")
    def submit_information(self, request, pk=None):
        g = self.get_object()
        members = g.members.filter(status="accepted", is_active=True)
        if members.count() < GROUP_MIN_SIZE:
            return Response(
                {
                    "success": False,
                    "message": f"Group size below min {GROUP_MIN_SIZE}",
                    "errors": {
                        "members": [f"Need at least {GROUP_MIN_SIZE} accepted members"]
                    },
                },
                status=400,
            )
        if members.count() > GROUP_MAX_SIZE:
            return Response(
                {
                    "success": False,
                    "message": f"Group size exceeds max {GROUP_MAX_SIZE}",
                },
                status=400,
            )
        for m in members:
            if not m.acknowledged:
                return Response(
                    {
                        "success": False,
                        "message": "All members must acknowledge undertaking",
                        "errors": {
                            "undertaking": [f"{m.student.email} not acknowledged"]
                        },
                    },
                    status=400,
                )
        from apps.projects.models import ProjectStage, Section
        from apps.submissions.models import Submission
        from apps.notifications.models import Notification
        from apps.audit.models import AuditLog

        stage = (
            ProjectStage.objects.filter(academic_year=g.academic_year)
            .order_by("order")
            .first()
            or ProjectStage.objects.order_by("order").first()
        )
        if not stage:
            return Response(
                {"success": False, "message": "Information stage not configured"},
                status=400,
            )
        sec, _ = Section.objects.get_or_create(
            group=g,
            stage=stage,
            section_type=stage.slug,
            defaults={
                "title": stage.name,
                "owner_role": "student",
                "content": {
                    "group_no": g.group_number,
                    "project_title": g.project.title if g.project else "",
                },
                "status": "draft",
            },
        )
        sec.status = "submitted"
        sec.save()
        sub, _ = Submission.objects.get_or_create(
            section=sec,
            group=g,
            submitted_by=request.user,
            defaults={"content": sec.content, "status": "submitted", "version": 1},
        )
        sub.status = "submitted"
        sub.submitted_at = timezone.now()
        sub.save()
        guide = g.guide_assignments.filter(is_active=True).first()
        if guide:
            Notification.objects.create(
                recipient=guide.faculty,
                notification_type="submission",
                title="Information submitted for verification",
                message=f"Group {g.group_number} submitted Information Stage for verification",
                related_type="submission",
                related_id=sub.id,
            )
        else:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            for hod in User.objects.filter(role__in=["hod", "admin"]):
                Notification.objects.create(
                    recipient=hod,
                    notification_type="submission",
                    title="Information submitted (no guide)",
                    message=f"Group {g.group_number} submitted Information — no guide assigned, HOD review needed",
                    related_type="submission",
                    related_id=sub.id,
                )
        AuditLog.objects.create(
            actor=request.user,
            actor_role=request.user.role,
            action="submission_submitted",
            entity_type="submission",
            entity_id=sub.id,
            new_value={"group": g.id, "stage": stage.id},
        )
        return Response(
            {
                "success": True,
                "data": {
                    "submission_id": sub.id,
                    "message": "Submitted for verification — guide/HOD notified, awaiting AccessGrant",
                },
            }
        )

    @action(detail=True, methods=["get"], url_path="invites")
    def invites(self, request, pk=None):
        g = self.get_object()
        pending = g.members.filter(status="invited")
        return Response(
            {"success": True, "data": GroupMemberSerializer(pending, many=True).data}
        )

    @action(detail=False, methods=["get"], url_path="my-invites")
    def my_invites(self, request):
        pending = GroupMember.objects.filter(student=request.user, status="invited")
        return Response(
            {"success": True, "data": GroupMemberSerializer(pending, many=True).data}
        )

    @action(detail=False, methods=["get"], url_path="search-students")
    def search_students(self, request):
        q = request.query_params.get("q", "")
        from apps.accounts.models import StudentProfile
        from django.contrib.auth import get_user_model

        User = get_user_model()
        if not q:
            return Response({"success": True, "data": []})
        users = User.objects.filter(role="student", email__icontains=q)[:10]
        profs = StudentProfile.objects.filter(roll_number__icontains=q)[:10]
        user_ids = set(
            list(users.values_list("id", flat=True))
            + list(profs.values_list("user_id", flat=True))
        )
        result = []
        for u in User.objects.filter(id__in=user_ids)[:10]:
            try:
                p = u.student_profile
                result.append(
                    {
                        "id": u.id,
                        "email": u.email,
                        "username": u.username,
                        "roll_number": p.roll_number,
                        "name": p.name,
                    }
                )
            except Exception:
                result.append(
                    {
                        "id": u.id,
                        "email": u.email,
                        "username": u.username,
                        "roll_number": "",
                        "name": u.username,
                    }
                )
        return Response({"success": True, "data": result})


class GroupMemberViewSet(viewsets.ModelViewSet):
    queryset = GroupMember.objects.all()
    serializer_class = GroupMemberSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        u = self.request.user
        if u.role == "student":
            return qs.filter(
                group__members__student=u, group__members__status="accepted"
            ).distinct()
        if u.role in ["faculty", "reviewer"]:
            return (
                qs.filter(group__guide_assignments__faculty=u).distinct()
                | qs.filter(group__reviewer_assignments__faculty=u).distinct()
            )
        return qs

    def perform_update(self, serializer):
        member = serializer.instance
        if member.group.is_locked:
            raise PermissionDenied({"message": "Group is locked — no edits allowed"})
        if self.request.user.role == "student" and not _is_group_member(
            self.request.user, member.group
        ):
            raise PermissionDenied({"message": "Cannot modify another group's members"})
        serializer.save()
        member.group.updated_by = self.request.user
        member.group.save(update_fields=["updated_at", "updated_by"])

    def perform_destroy(self, instance):
        if instance.group.is_locked:
            raise PermissionDenied(
                {"message": "Group is locked — cannot remove members"}
            )
        if self.request.user.role == "student" and not _is_group_member(
            self.request.user, instance.group
        ):
            raise PermissionDenied({"message": "Cannot modify another group"})
        instance.delete()
        instance.group.updated_by = self.request.user
        instance.group.save(update_fields=["updated_at", "updated_by"])
        from apps.audit.models import AuditLog

        AuditLog.objects.create(
            actor=self.request.user,
            actor_role=self.request.user.role,
            action="student_removed",
            entity_type="group_member",
            entity_id=instance.id,
            new_value={"email": instance.student.email},
        )


class GuideAssignmentViewSet(viewsets.ModelViewSet):
    queryset = ProjectGuideAssignment.objects.all()
    serializer_class = GuideAssignmentSerializer


class ReviewerAssignmentViewSet(viewsets.ModelViewSet):
    queryset = ReviewerAssignment.objects.all()
    serializer_class = ReviewerAssignmentSerializer
