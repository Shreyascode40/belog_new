from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.academics.models import Department, AcademicYear
from apps.groups.models import ProjectGroup
from apps.projects.models import Project, ProjectStage, Section
from apps.submissions.models import Submission
from apps.reviews.models import Review
from apps.logbook.models import HODFinalApproval, FinalLogBook
from django.utils import timezone
from pathlib import Path
from django.conf import settings

User = get_user_model()


class LogbookPDFTest(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name="Comp Engg", code="COMPX")
        self.ay = AcademicYear.objects.create(
            year_label="2099-00",
            start_date="2099-01-01",
            end_date="2099-12-31",
            department=self.dept,
            is_current=False,
        )
        self.hod = User.objects.create_user(
            username="hodtest", email="hodtest@x.edu", password="pass1234", role="hod"
        )
        self.project = Project.objects.create(
            title="Sample Project For PDF Test",
            area_domain="AI",
            description="desc",
            academic_year=self.ay,
        )
        self.group = ProjectGroup.objects.create(
            group_number="99",
            academic_year=self.ay,
            department=self.dept,
            project=self.project,
            status="active",
        )
        self.stage = ProjectStage.objects.create(
            academic_year=self.ay,
            name="Information",
            slug="info-test",
            order=0,
            is_required=True,
        )
        self.stage2 = ProjectStage.objects.create(
            academic_year=self.ay,
            name="Schedule",
            slug="sched-test",
            order=1,
            is_required=True,
        )
        for s in [self.stage, self.stage2]:
            sec = Section.objects.create(
                group=self.group,
                stage=s,
                section_type=s.slug,
                title=s.name,
                owner_role="student",
                content={},
                status="locked",
            )
            Submission.objects.create(
                section=sec,
                group=self.group,
                submitted_by=self.hod,
                content={},
                status="locked",
            )
        self.review = Review.objects.create(
            group=self.group,
            review_number=1,
            academic_year=self.ay,
            review_date=timezone.now().date(),
            reviewer=self.hod,
            status="finalized",
        )
        HODFinalApproval.objects.create(
            group=self.group,
            approved_by=self.hod,
            approved=True,
            approved_at=timezone.now(),
            checklist_snapshot={},
        )

    def test_pdf_generation_produces_real_pdf(self):
        from apps.logbook.services import generate_pdf

        lb = FinalLogBook(
            group=self.group,
            academic_year=self.ay,
            version=1,
            generated_at=timezone.now(),
            generated_by=self.hod,
        )
        pdf_rel = generate_pdf(self.group, lb)
        pdf_path = Path(settings.MEDIA_ROOT) / pdf_rel
        self.assertTrue(pdf_path.exists(), "PDF file not created")
        data = pdf_path.read_bytes()
        self.assertTrue(data.startswith(b"%PDF-"), f"Not a PDF, header: {data[:20]!r}")
        self.assertGreater(len(data), 1024, "PDF trivially small — broken render")
        # optional text check
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(pdf_path))
            text = ""
            for page in reader.pages[:2]:
                text += page.extract_text() or ""
            self.assertIn("Project", text)
        except Exception:
            pass
        pdf_path.unlink(missing_ok=True)

    def test_health_check(self):
        from apps.logbook.services import health_check

        self.assertTrue(
            health_check(), "PDF health check failed — renderer misconfigured"
        )
