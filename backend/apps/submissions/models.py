from django.db import models
from django.conf import settings
from django.utils import timezone


class SubmissionStatus:
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    CHANGES_REQUIRED = "changes_required"
    RESUBMITTED = "resubmitted"
    APPROVED = "approved"
    LOCKED = "locked"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

    CHOICES = (
        (DRAFT, "Draft"),
        (SUBMITTED, "Submitted"),
        (UNDER_REVIEW, "Under Review"),
        (CHANGES_REQUIRED, "Changes Required"),
        (RESUBMITTED, "Resubmitted"),
        (APPROVED, "Approved"),
        (LOCKED, "Locked"),
        (OVERDUE, "Overdue"),
        (CANCELLED, "Cancelled"),
    )


class Submission(models.Model):
    section = models.ForeignKey(
        "projects.Section", on_delete=models.CASCADE, related_name="submissions"
    )
    group = models.ForeignKey(
        "groups.ProjectGroup", on_delete=models.CASCADE, related_name="submissions"
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="submissions"
    )
    content = models.JSONField(default=dict)
    status = models.CharField(
        max_length=20, choices=SubmissionStatus.CHOICES, default=SubmissionStatus.DRAFT
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_submissions",
    )
    review_remarks = models.TextField(blank=True)
    version = models.IntegerField(default=1)
    is_latest = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "submission"
        ordering = ["-submitted_at", "-created_at"]

    def __str__(self):
        return f"Submission v{self.version} - {self.section.title} - Group {self.group.group_number}"

    @property
    def can_transition(self):
        valid_transitions = {
            SubmissionStatus.DRAFT: [SubmissionStatus.SUBMITTED],
            SubmissionStatus.SUBMITTED: [
                SubmissionStatus.UNDER_REVIEW,
                SubmissionStatus.CHANGES_REQUIRED,
            ],
            SubmissionStatus.UNDER_REVIEW: [
                SubmissionStatus.APPROVED,
                SubmissionStatus.CHANGES_REQUIRED,
            ],
            SubmissionStatus.CHANGES_REQUIRED: [SubmissionStatus.RESUBMITTED],
            SubmissionStatus.RESUBMITTED: [SubmissionStatus.UNDER_REVIEW],
            SubmissionStatus.APPROVED: [SubmissionStatus.LOCKED],
        }
        return valid_transitions.get(self.status, [])


class SubmissionVersion(models.Model):
    submission = models.ForeignKey(
        Submission, on_delete=models.CASCADE, related_name="versions"
    )
    version_number = models.IntegerField()
    content = models.JSONField(default=dict)
    review_remark = models.TextField(blank=True)
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "submission_version"
        unique_together = ["submission", "version_number"]
        ordering = ["version_number"]

    def __str__(self):
        return f"Version {self.version_number} - Submission {self.submission.id}"
