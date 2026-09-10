from django.db import models
from django.conf import settings
from django.utils import timezone


class Project(models.Model):
    TECHNOLOGY_CHOICES = (
        ("web", "Web Application"),
        ("mobile", "Mobile Application"),
        ("desktop", "Desktop Application"),
        ("iot", "IoT/Embedded"),
        ("ai/ml", "AI/ML"),
        ("cloud", "Cloud Computing"),
        ("data", "Data Science"),
        ("cybersecurity", "Cybersecurity"),
        ("other", "Other"),
    )

    academic_year = models.ForeignKey(
        "academics.AcademicYear", on_delete=models.CASCADE, related_name="projects"
    )
    title = models.CharField(max_length=500)
    area_domain = models.CharField(max_length=300)
    description = models.TextField()
    technology_stack = models.CharField(max_length=500, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "project"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class ProjectStage(models.Model):
    STAGE_TYPE_CHOICES = (
        ("information", "Information"),
        ("schedule", "Schedule"),
        ("review", "Review"),
        ("design", "Design"),
        ("development", "Development"),
        ("testing", "Testing"),
        ("submission", "Submission"),
        ("final", "Final"),
        ("document", "Document"),
    )

    academic_year = models.ForeignKey(
        "academics.AcademicYear", on_delete=models.CASCADE, related_name="stages"
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    stage_type = models.CharField(
        max_length=20, choices=STAGE_TYPE_CHOICES, default="information"
    )
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    is_required = models.BooleanField(default=True)
    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "project_stage"
        ordering = ["academic_year", "order"]
        unique_together = ["academic_year", "slug"]

    def __str__(self):
        return f"{self.name} ({self.academic_year.year_label})"


class StageDependency(models.Model):
    DEPENDENCY_TYPE_CHOICES = (
        ("prerequisite", "Prerequisite"),
        ("parallel", "Parallel"),
    )

    stage = models.ForeignKey(
        "ProjectStage", on_delete=models.CASCADE, related_name="dependencies"
    )
    depends_on = models.ForeignKey(
        "ProjectStage", on_delete=models.CASCADE, related_name="dependents"
    )
    dependency_type = models.CharField(
        max_length=20, choices=DEPENDENCY_TYPE_CHOICES, default="prerequisite"
    )

    class Meta:
        db_table = "stage_dependency"
        unique_together = ["stage", "depends_on"]

    def __str__(self):
        return f"{self.stage.name} depends on {self.depends_on.name}"


class Section(models.Model):
    SECTION_STATUS_CHOICES = (
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("under_review", "Under Review"),
        ("approved", "Approved"),
        ("locked", "Locked"),
        ("changes_required", "Changes Required"),
    )

    stage = models.ForeignKey(
        "ProjectStage", on_delete=models.CASCADE, related_name="sections"
    )
    group = models.ForeignKey(
        "groups.ProjectGroup", on_delete=models.CASCADE, related_name="sections"
    )
    section_type = models.CharField(max_length=100)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    is_required = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    owner_role = models.CharField(max_length=20)
    content = models.JSONField(default=dict)
    status = models.CharField(
        max_length=20, choices=SECTION_STATUS_CHOICES, default="draft"
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="section_approvals",
    )
    version = models.IntegerField(default=1)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "section"
        unique_together = ["stage", "group", "section_type"]
        ordering = ["order"]

    def __str__(self):
        return f"{self.title} - Group {self.group.group_number}"


class Activity(models.Model):
    section = models.ForeignKey(
        "Section", on_delete=models.CASCADE, related_name="activities"
    )
    title = models.CharField(max_length=500)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    completed = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "activity"
        ordering = ["order"]

    def __str__(self):
        return self.title
