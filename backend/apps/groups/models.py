from django.db import models
from django.conf import settings
from django.utils import timezone


class ProjectGroup(models.Model):
    STATUS_CHOICES = (
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("completed", "Completed"),
        ("archived", "Archived"),
    )

    academic_year = models.ForeignKey(
        "academics.AcademicYear", on_delete=models.CASCADE, related_name="groups"
    )
    department = models.ForeignKey(
        "academics.Department", on_delete=models.CASCADE, related_name="groups"
    )
    group_number = models.CharField(max_length=20)
    project = models.OneToOneField(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="group",
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    current_stage = models.ForeignKey(
        "projects.ProjectStage",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="current_groups",
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "project_group"
        ordering = ["group_number"]
        unique_together = ["academic_year", "group_number", "department"]

    def __str__(self):
        return f"Group {self.group_number} - {self.academic_year.year_label}"

    @property
    def progress(self):
        from apps.projects.models import ProjectStage
        from apps.submissions.models import Submission

        stages = ProjectStage.objects.filter(
            academic_year=self.academic_year, is_required=True
        )
        completed = 0
        for stage in stages:
            submissions = Submission.objects.filter(
                section__stage=stage, group=self
            ).order_by("-submitted_at")
            if submissions.exists() and submissions.first().status in [
                "approved",
                "locked",
            ]:
                completed += 1
        total = stages.count()
        return round((completed / total * 100), 1) if total > 0 else 0


class GroupMember(models.Model):
    ROLE_CHOICES = (
        ("leader", "Leader"),
        ("member", "Member"),
    )
    STATUS_CHOICES = (
        ("invited", "Invited"),
        ("accepted", "Accepted"),
        ("declined", "Declined"),
    )

    group = models.ForeignKey(
        ProjectGroup, on_delete=models.CASCADE, related_name="members"
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="group_memberships",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="member")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="accepted")
    te_result = models.CharField(max_length=50, blank=True)
    contribution = models.TextField(blank=True)
    acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    photo = models.ImageField(upload_to="students/photos/", null=True, blank=True)
    joined_date = models.DateField(default=timezone.localdate)
    left_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "group_member"
        ordering = ["-joined_date"]
        unique_together = ["group", "student"]

    def __str__(self):
        return f"{self.student.email} in Group {self.group.group_number}"


class ProjectGuideAssignment(models.Model):
    group = models.ForeignKey(
        ProjectGroup, on_delete=models.CASCADE, related_name="guide_assignments"
    )
    faculty = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="guide_assignments",
    )
    academic_year = models.ForeignKey(
        "academics.AcademicYear", on_delete=models.CASCADE
    )
    assigned_date = models.DateField(default=timezone.localdate)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "project_guide_assignment"
        ordering = ["-assigned_date"]
        unique_together = ["group", "faculty", "academic_year"]

    def __str__(self):
        return f"Guide {self.faculty.email} for Group {self.group.group_number}"


class ReviewerAssignment(models.Model):
    REVIEW_TYPE_CHOICES = (
        ("internal", "Internal"),
        ("external", "External"),
    )

    group = models.ForeignKey(
        ProjectGroup, on_delete=models.CASCADE, related_name="reviewer_assignments"
    )
    faculty = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviewer_assignments",
    )
    academic_year = models.ForeignKey(
        "academics.AcademicYear", on_delete=models.CASCADE
    )
    review_number = models.IntegerField(default=1)
    assignment_type = models.CharField(
        max_length=20, choices=REVIEW_TYPE_CHOICES, default="internal"
    )
    assigned_date = models.DateField(default=timezone.localdate)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "reviewer_assignment"
        ordering = ["-assigned_date"]
        unique_together = ["group", "faculty", "academic_year", "review_number"]

    def __str__(self):
        return f"Reviewer {self.faculty.email} for Group {self.group.group_number} - Review {self.review_number}"
