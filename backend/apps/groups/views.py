from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
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
)

GROUP_MIN_SIZE = int(getattr(settings, "GROUP_MIN_SIZE", 2))
GROUP_MAX_SIZE = int(getattr(settings, "GROUP_MAX_SIZE", 4))


class ProjectGroupViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectGroupSerializer

    def get_queryset(self):
        qs = ProjectGroup.objects.all()
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

    def perform_create(self, serializer):
        user = self.request.user
        data = self.request.data
        # prevent student already in active group same AY
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
        # check double group
        if user.role == "student":
            if GroupMember.objects.filter(
                student=user,
                group__academic_year=ay,
                group__is_active=True,
                status="accepted",
            ).exists():
                from rest_framework.exceptions import ValidationError

                raise ValidationError(
                    {
                        "group": [
                            "You are already active in a group for this academic year"
                        ]
                    }
                )
        # auto group number
        existing = ProjectGroup.objects.filter(
            academic_year=ay, department=dept
        ).order_by("-group_number")
        max_num = 0
        for g in existing:
            try:
                max_num = max(max_num, int(g.group_number))
            except:
                pass
        group_number = str(max_num + 1).zfill(2)
        # create project
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
        )
        # add creator as member 1 — auto-fetch all previous info from StudentProfile
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
        # handle invited members if provided as list of emails/rolls
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
            except:
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

                prof = StudentProfile.objects.filter(roll_number=roll).first()
                if prof:
                    target = prof.user
            if target:
                if GroupMember.objects.filter(
                    student=target,
                    group__academic_year=ay,
                    group__is_active=True,
                    status="accepted",
                ).exists():
                    continue
                # auto-fetch target's StudentProfile for previous info
                try:
                    tprof = target.student_profile
                    te = te or tprof.roll_number or ""
                except:
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
        return group

    @action(detail=True, methods=["post"], url_path="add-member-direct")
    def add_member_direct(self, request, pk=None):
        g = self.get_object()
        data = request.data
        if g.members.filter(status="accepted").count() >= GROUP_MAX_SIZE:
            return Response(
                {
                    "success": False,
                    "message": f"Group size exceeds max {GROUP_MAX_SIZE}",
                },
                status=400,
            )
        email = data.get("email")
        if not email:
            return Response({"success": False, "message": "Email required"}, status=400)
        from django.contrib.auth import get_user_model
        from apps.accounts.models import StudentProfile

        User = get_user_model()
        user, created = User.objects.get_or_create(
            email=email, defaults={"username": email.split("@")[0], "role": "student"}
        )
        if created:
            user.set_password("pass1234")
            user.save()
        # auto-fetch / create profile with provided fields — direct fill like registration
        prof, _ = StudentProfile.objects.get_or_create(
            user=user,
            defaults={
                "name": data.get("name", ""),
                "roll_number": data.get("roll_number", ""),
                "mobile": data.get("mobile", ""),
                "exam_seat_number": data.get("exam_seat_number", ""),
                "email": email,
                "department": g.department.name
                if g.department
                else "Computer Engineering",
                "academic_year": g.academic_year,
            },
        )
        # update with latest provided values (direct fill)
        for field in ["name", "roll_number", "mobile", "exam_seat_number", "email"]:
            if data.get(field):
                setattr(prof, field, data.get(field))
        prof.save()
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
        member = GroupMember.objects.create(
            group=g,
            student=user,
            role="member",
            status="accepted",
            te_result=data.get("te_result", ""),
            contribution=data.get("contribution", ""),
        )
        return Response(
            {"success": True, "data": GroupMemberSerializer(member).data}, status=201
        )

    @action(detail=True, methods=["post"], url_path="add-member")
    def add_member(self, request, pk=None):
        g = self.get_object()
        data = {**request.data, "group": g.id, "status": "invited"}
        s = GroupMemberSerializer(data=data)
        s.is_valid(raise_exception=True)
        # check double group
        student_id = request.data.get("student")
        from apps.academics.models import AcademicYear

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
        if g.members.filter(status="accepted").count() >= GROUP_MAX_SIZE:
            return Response(
                {
                    "success": False,
                    "message": f"Group size exceeds max {GROUP_MAX_SIZE}",
                },
                status=400,
            )
        obj = s.save()
        # auto-fetch from StudentProfile if member info blank — fetch previous info
        try:
            prof = obj.student.student_profile
            updated = False
            if not obj.te_result and getattr(prof, "roll_number", ""):
                obj.te_result = prof.roll_number
                updated = True
            if not obj.contribution and getattr(prof, "name", ""):
                obj.contribution = ""
                updated = True
            if updated:
                obj.save()
        except:
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
        from django.utils import timezone

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
        # allow editing contribution/photo at acknowledge time
        if "contribution" in request.data:
            m.contribution = request.data["contribution"]
        if "te_result" in request.data:
            m.te_result = request.data["te_result"]
        m.save()
        return Response({"success": True, "data": GroupMemberSerializer(m).data})

    @action(detail=True, methods=["post"], url_path="submit-information")
    def submit_information(self, request, pk=None):
        g = self.get_object()
        # validation
        members = g.members.filter(status="accepted")
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
        # check all required member fields
        for m in members:
            prof = getattr(m.student, "student_profile", None)
            if (
                not prof
                or not prof.roll_number
                or not prof.mobile
                or not prof.exam_seat_number
            ):
                # try GroupMember fields
                if not m.te_result and not prof:
                    pass
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
            if not m.contribution and not m.te_result:
                # allow contribution to be edited later, but require at least one
                pass
        # check required member fields filled
        incomplete = []
        for m in members:
            if not m.te_result:
                incomplete.append(f"{m.student.email} missing TE Result")
        # For now, TE Result is required if configured, but allow empty for sample
        # Proceed to create Section/Submission for Information stage (order 0)
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
        # notify guide or HOD
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
        # also search by roll
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
            except:
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


class GuideAssignmentViewSet(viewsets.ModelViewSet):
    queryset = ProjectGuideAssignment.objects.all()
    serializer_class = GuideAssignmentSerializer


class ReviewerAssignmentViewSet(viewsets.ModelViewSet):
    queryset = ReviewerAssignment.objects.all()
    serializer_class = ReviewerAssignmentSerializer
