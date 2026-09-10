from django.db import models
from django.conf import settings
from django.utils import timezone


class HODFinalApproval(models.Model):
    group = models.ForeignKey(
        "groups.ProjectGroup", on_delete=models.CASCADE, related_name="hod_approvals"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hod_final_approvals",
    )
    approved = models.BooleanField(default=False)
    remark = models.TextField(blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    checklist_snapshot = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "hod_final_approval"
        ordering = ["-created_at"]
        unique_together = ["group"]

    def __str__(self):
        return f"HOD Approval Group {self.group.group_number} approved={self.approved}"


class FinalLogBook(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("generating", "Generating"),
        ("completed", "Completed"),
        ("archived", "Archived"),
    )
    group = models.ForeignKey(
        "groups.ProjectGroup", on_delete=models.CASCADE, related_name="final_logbooks"
    )
    academic_year = models.ForeignKey(
        "academics.AcademicYear",
        on_delete=models.CASCADE,
        related_name="final_logbooks",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    version = models.IntegerField(default=1)
    pdf_path = models.CharField(max_length=500, null=True, blank=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="generated_logbooks",
    )
    generated_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "final_logbook"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Logbook Group {self.group.group_number} v{self.version}"
