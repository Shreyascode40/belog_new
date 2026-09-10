from django.db import models
from django.conf import settings
from django.utils import timezone



class AuditAction:
    USER_CREATED = "user_created"
    USER_DEACTIVATED = "user_deactivated"
    GROUP_CREATED = "group_created"
    STUDENT_ADDED = "student_added"
    STUDENT_REMOVED = "student_removed"
    GUIDE_ASSIGNED = "guide_assigned"
    REVIEWER_ASSIGNED = "reviewer_assigned"
    REVIEWER_REASSIGNED = "reviewer_reassigned"
    SUBMISSION_CREATED = "submission_created"
    SUBMISSION_EDITED = "submission_edited"
    SUBMISSION_SUBMITTED = "submission_submitted"
    SUBMISSION_APPROVED = "submission_approved"
    CHANGES_REQUESTED = "changes_requested"
    SUBMISSION_RESUBMITTED = "submission_resubmitted"
    MARKS_ENTERED = "marks_entered"
    MARKS_FINALIZED = "marks_finalized"
    MARKS_CORRECTED = "marks_corrected"
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_REPLACED = "document_replaced"
    STAGE_UNLOCKED = "stage_unlocked"
    STAGE_LOCKED = "stage_locked"
    FINAL_SUBMISSION_APPROVED = "final_submission_approved"
    GROUP_ARCHIVED = "group_archived"
    REPORT_GENERATED = "report_generated"
    LOGBOOK_GENERATED = "logbook_generated"

    CHOICES = (
        (USER_CREATED, "User Created"),
        (USER_DEACTIVATED, "User Deactivated"),
        (GROUP_CREATED, "Group Created"),
        (STUDENT_ADDED, "Student Added to Group"),
        (STUDENT_REMOVED, "Student Removed from Group"),
        (GUIDE_ASSIGNED, "Guide Assigned"),
        (REVIEWER_ASSIGNED, "Reviewer Assigned"),
        (REVIEWER_REASSIGNED, "Reviewer Reassigned"),
        (SUBMISSION_CREATED, "Submission Created"),
        (SUBMISSION_EDITED, "Submission Edited"),
        (SUBMISSION_SUBMITTED, "Submission Submitted"),
        (SUBMISSION_APPROVED, "Submission Approved"),
        (CHANGES_REQUESTED, "Changes Requested"),
        (SUBMISSION_RESUBMITTED, "Submission Resubmitted"),
        (MARKS_ENTERED, "Marks Entered"),
        (MARKS_FINALIZED, "Marks Finalized"),
        (MARKS_CORRECTED, "Marks Corrected"),
        (DOCUMENT_UPLOADED, "Document Uploaded"),
        (DOCUMENT_REPLACED, "Document Replaced"),
        (STAGE_UNLOCKED, "Stage Unlocked"),
        (STAGE_LOCKED, "Stage Locked"),
        (FINAL_SUBMISSION_APPROVED, "Final Submission Approved"),
        (GROUP_ARCHIVED, "Group Archived"),
        (REPORT_GENERATED, "Report Generated"),
        (LOGBOOK_GENERATED, "Logbook Generated"),
    )


class AuditLog(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="audit_logs"
    )
    actor_role = models.CharField(max_length=20)
    action = models.CharField(max_length=50, choices=AuditAction.CHOICES)
    entity_type = models.CharField(max_length=100)
    entity_id = models.BigIntegerField()
    previous_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "audit_log"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["-timestamp"]),
            models.Index(fields=["actor", "action"]),
            models.Index(fields=["entity_type", "entity_id"]),
        ]

    def __str__(self):
        return (
            f"{self.actor.email} - {self.action} - {self.entity_type} {self.entity_id}"
        )


class Deadline(models.Model):
    stage = models.ForeignKey(
        "projects.ProjectStage", on_delete=models.CASCADE, related_name="deadlines"
    )
    academic_year = models.ForeignKey(
        "academics.AcademicYear", on_delete=models.CASCADE, related_name="deadlines"
    )
    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "deadline"
        unique_together = ["stage", "academic_year"]

    def __str__(self):
        return f"{self.stage.name} - {self.due_date}"
