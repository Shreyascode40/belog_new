from django.db import models
from django.conf import settings
from django.utils import timezone


class Report(models.Model):
    REPORT_FORMAT = (("csv", "CSV"), ("excel", "Excel"), ("pdf", "PDF"))
    REPORT_CHOICES = (
        ("progress", "Progress"),
        ("faculty_workload", "Faculty Workload"),
        ("reviewer_workload", "Reviewer Workload"),
        ("stage_completion", "Stage Completion"),
        ("overdue", "Overdue"),
        ("marks", "Marks"),
        ("final_submission", "Final Submission"),
        ("co_attainment", "CO Attainment"),
        ("po_attainment", "PO Attainment"),
        ("department_status", "Department Status"),
    )
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reports"
    )
    report_type = models.CharField(
        max_length=50, choices=REPORT_CHOICES, default="progress"
    )
    title = models.CharField(max_length=500)
    academic_year = models.ForeignKey(
        "academics.AcademicYear", on_delete=models.CASCADE, null=True, blank=True
    )
    filters = models.JSONField(default=dict)
    format = models.CharField(max_length=10, choices=REPORT_FORMAT, default="pdf")
    file_path = models.CharField(max_length=500, null=True, blank=True)
    status = models.CharField(max_length=20, default="generated")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "report"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.report_type})"
