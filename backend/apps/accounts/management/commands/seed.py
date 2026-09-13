from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.academics.models import Department, AcademicYear
from apps.groups.models import (
    ProjectGroup,
    GroupMember,
    ProjectGuideAssignment,
    ReviewerAssignment,
)
from apps.projects.models import Project, ProjectStage
from apps.co_po.models import CO, PO, COPOMapping
from django.utils import timezone
from datetime import date, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = "Seed development data"

    def handle(self, *args, **options):
        self.stdout.write("Seeding...")
        dept, _ = Department.objects.get_or_create(
            code="COMP", defaults={"name": "Computer Engineering"}
        )
        ay, _ = AcademicYear.objects.get_or_create(
            year_label="2025-26",
            defaults={
                "start_date": date(2025, 7, 1),
                "end_date": date(2026, 6, 30),
                "department": dept,
                "is_current": True,
            },
        )
        users = []

        def create_user(email, username, role, pwd="pass1234"):
            u = User.objects.filter(email__iexact=email).first()
            if u:
                u.role = role
                u.is_active = True
                u.save(update_fields=["role", "is_active"])
                return u
            uname = username
            base = uname
            i = 0
            while User.objects.filter(username__iexact=uname).exists():
                i += 1
                uname = f"{base}{i}"
            u = User.objects.create_user(
                username=uname, email=email.lower(), password=pwd, role=role
            )
            u.is_active = True
            u.save(update_fields=["is_active"])
            return u

        hod = create_user("hod@college.edu", "hod", "hod")
        hod.is_staff = True
        hod.save()
        f1 = create_user("guide1@college.edu", "guide1", "faculty")
        f2 = create_user("guide2@college.edu", "guide2", "faculty")
        rev = create_user("reviewer@college.edu", "reviewer", "reviewer")
        s1 = create_user("s1@student.edu", "s1", "student")
        s2 = create_user("s2@student.edu", "s2", "student")
        s3 = create_user("s3@student.edu", "s3", "student")
        s4 = create_user("s4@student.edu", "s4", "student")
        from apps.accounts.models import StudentProfile, FacultyProfile

        for u, roll, name in [
            (s1, "41001", "Aarav Sharma"),
            (s2, "41002", "Priya Patil"),
            (s3, "41003", "Rohan Desai"),
            (s4, "41004", "Sneha Kulkarni"),
        ]:
            StudentProfile.objects.get_or_create(
                user=u,
                defaults={
                    "roll_number": roll,
                    "name": name,
                    "department": "COMP",
                    "exam_seat_number": f"SEAT{roll}",
                },
            )
        for u, eid, name in [
            (f1, "EMP101", "Dr. A. Kumar"),
            (f2, "EMP102", "Prof. B. Singh"),
            (rev, "EMP201", "Dr. Reviewer"),
        ]:
            FacultyProfile.objects.get_or_create(
                user=u,
                defaults={
                    "employee_id": eid,
                    "name": name,
                    "designation": "Professor",
                    "department": "COMP",
                },
            )
        stages_data = [
            ("Project Information", "project-info", 1),
            ("Group Information", "group-info", 2),
            ("Student Information", "student-info", 3),
            ("Project Schedule", "schedule", 4),
            ("Topic Finalization", "topic", 5),
            ("Activities", "activities", 6),
            ("Review 1", "review-1", 7),
            ("Requirement Analysis", "req-analysis", 8),
            ("Design/UML", "design", 9),
            ("Review 2", "review-2", 10),
            ("Development", "development", 11),
            ("Testing", "testing", 12),
            ("Review 3", "review-3", 13),
            ("Competition/Publications", "competition", 14),
            ("Term-I/Term-II", "term", 15),
            ("Final Submission", "final-sub", 16),
            ("Final Verification", "final-verify", 17),
            ("Log Book Generation", "logbook", 18),
        ]
        for name, slug, order in stages_data:
            ProjectStage.objects.get_or_create(
                academic_year=ay,
                slug=slug,
                defaults={
                    "name": name,
                    "order": order,
                    "is_required": True,
                    "start_date": date.today(),
                    "due_date": date.today() + timedelta(days=60),
                },
            )
        for co_code, co_name in [
            ("CO1", "Problem Analysis"),
            ("CO2", "Design"),
            ("CO3", "Implementation"),
            ("CO4", "Project Management"),
        ]:
            CO.objects.get_or_create(
                code=co_code,
                defaults={"name": co_name, "department": dept, "academic_year": ay},
            )
        for po_code, po_name in [
            ("PO1", "Engineering Knowledge"),
            ("PO2", "Problem Analysis"),
            ("PO3", "Design"),
            ("PO4", "Project Mgmt"),
        ]:
            PO.objects.get_or_create(
                code=po_code,
                defaults={"name": po_name, "department": dept, "academic_year": ay},
            )
        for co in CO.objects.all():
            for po in PO.objects.all()[:2]:
                COPOMapping.objects.get_or_create(
                    co=co, po=po, defaults={"weightage": 3}
                )
        proj1, _ = Project.objects.get_or_create(
            title="AI Based Logbook System",
            defaults={
                "area_domain": "AI/ML",
                "description": "Digital logbook",
                "academic_year": ay,
            },
        )
        proj2, _ = Project.objects.get_or_create(
            title="IoT Smart Campus",
            defaults={
                "area_domain": "IoT",
                "description": "Smart campus",
                "academic_year": ay,
            },
        )
        g1, _ = ProjectGroup.objects.get_or_create(
            group_number="01",
            academic_year=ay,
            department=dept,
            defaults={"status": "active"},
        )
        g2, _ = ProjectGroup.objects.get_or_create(
            group_number="02",
            academic_year=ay,
            department=dept,
            defaults={"status": "active"},
        )
        if not g1.project:
            g1.project = proj1
            g1.save()
        if not g2.project:
            g2.project = proj2
            g2.save()
        GroupMember.objects.get_or_create(
            group=g1, student=s1, defaults={"role": "leader"}
        )
        GroupMember.objects.get_or_create(
            group=g1, student=s2, defaults={"role": "member"}
        )
        GroupMember.objects.get_or_create(
            group=g2, student=s3, defaults={"role": "leader"}
        )
        GroupMember.objects.get_or_create(
            group=g2, student=s4, defaults={"role": "member"}
        )
        ProjectGuideAssignment.objects.get_or_create(
            group=g1, faculty=f1, academic_year=ay, defaults={"is_active": True}
        )
        ProjectGuideAssignment.objects.get_or_create(
            group=g2, faculty=f2, academic_year=ay, defaults={"is_active": True}
        )
        ReviewerAssignment.objects.get_or_create(
            group=g1, faculty=rev, academic_year=ay, review_number=1
        )
        ReviewerAssignment.objects.get_or_create(
            group=g2, faculty=rev, academic_year=ay, review_number=1
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Seed complete. Credentials: hod@college.edu / pass1234, guide1@college.edu / pass1234, s1@student.edu / pass1234"
            )
        )
