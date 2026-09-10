from django.db import models
from django.conf import settings
from django.utils import timezone


class ReviewStatus:
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FINALIZED = "finalized"
    CORRECTION_REQUESTED = "correction_requested"
    CORRECTED = "corrected"

    CHOICES = (
        (DRAFT, "Draft"),
        (IN_PROGRESS, "In Progress"),
        (COMPLETED, "Completed"),
        (FINALIZED, "Finalized"),
        (CORRECTION_REQUESTED, "Correction Requested"),
        (CORRECTED, "Corrected"),
    )


class Review(models.Model):
    REVIEW_NUMBER_CHOICES = (
        (1, "Review 1"),
        (2, "Review 2"),
        (3, "Review 3"),
    )

    group = models.ForeignKey(
        "groups.ProjectGroup", on_delete=models.CASCADE, related_name="reviews"
    )
    review_number = models.IntegerField(choices=REVIEW_NUMBER_CHOICES)
    academic_year = models.ForeignKey(
        "academics.AcademicYear", on_delete=models.CASCADE, related_name="reviews"
    )
    stage = models.ForeignKey(
        "projects.ProjectStage",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reviews",
    )
    review_date = models.DateField()
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews_given"
    )
    status = models.CharField(
        max_length=20, choices=ReviewStatus.CHOICES, default=ReviewStatus.DRAFT
    )
    total_max_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    total_obtained_marks = models.DecimalField(
        max_digits=6, decimal_places=2, default=0
    )
    overall_remarks = models.TextField(blank=True)
    finalized_at = models.DateTimeField(null=True, blank=True)
    finalized_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="finalized_reviews",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "review"
        unique_together = ["group", "review_number", "academic_year"]
        ordering = ["review_number"]

    def __str__(self):
        return f"Review {self.review_number} - Group {self.group.group_number}"

    @property
    def is_finalizable(self):
        return (
            all(criterion.marks_set.exists() for criterion in self.criteria.all())
            and self.status == ReviewStatus.COMPLETED
        )


class ReviewCriterion(models.Model):
    review = models.ForeignKey(
        Review, on_delete=models.CASCADE, related_name="criteria"
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    max_marks = models.DecimalField(max_digits=6, decimal_places=2)
    weightage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    co = models.ForeignKey(
        "co_po.CO",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="review_criteria",
    )
    po = models.ForeignKey(
        "co_po.PO",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="review_criteria",
    )
    is_required = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "review_criterion"
        ordering = ["order"]

    def __str__(self):
        return f"{self.name} (Max: {self.max_marks})"


class Mark(models.Model):
    MARK_STATUS_CHOICES = (
        ("draft", "Draft"),
        ("saved", "Saved"),
        ("submitted", "Submitted"),
        ("finalized", "Finalized"),
        ("correction_requested", "Correction Requested"),
        ("corrected", "Corrected"),
    )

    criterion = models.ForeignKey(
        ReviewCriterion, on_delete=models.CASCADE, related_name="marks_set"
    )
    group = models.ForeignKey(
        "groups.ProjectGroup", on_delete=models.CASCADE, related_name="marks"
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="marks_given"
    )
    obtained_marks = models.DecimalField(max_digits=6, decimal_places=2)
    remarks = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=MARK_STATUS_CHOICES, default=MARK_STATUS_CHOICES[0][0]
    )
    is_finalized = models.BooleanField(default=False)
    finalized_at = models.DateTimeField(null=True, blank=True)
    finalized_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "mark"
        unique_together = ["criterion", "group", "reviewer"]
        ordering = ["criterion__order"]

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.obtained_marks < 0:
            raise ValidationError({"obtained_marks": "Marks cannot be negative."})
        if self.obtained_marks > self.criterion.max_marks:
            raise ValidationError({"obtained_marks": "Marks cannot exceed maximum."})


class Approval(models.Model):
    DECISION_CHOICES = (
        ("approved", "Approved"),
        ("changes_required", "Changes Required"),
        ("rejected", "Rejected"),
    )

    submission = models.ForeignKey(
        "submissions.Submission", on_delete=models.CASCADE, related_name="approvals"
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="approvals_given",
    )
    role = models.CharField(max_length=20)
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES)
    remark = models.TextField(blank=True)
    decided_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "approval"
        ordering = ["-decided_at"]

    def __str__(self):
        return f"{self.decision} - {self.submission.id} by {self.approver.email}"
