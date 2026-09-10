from django.db import models
from django.conf import settings
from django.utils import timezone


class DocumentType:
    PHOTOGRAPH = "photograph"
    SYNOPSIS = "synopsis"
    REPORT = "report"
    UML = "uml_diagram"
    RESEARCH_PAPER = "research_paper"
    CERTIFICATE = "certificate"
    COMPETITION_CERT = "competition_certificate"
    SPONSORSHIP_LETTER = "sponsorship_letter"
    COMPLETION_LETTER = "completion_letter"
    PPT = "ppt"
    SOURCE_CODE = "source_code"
    OTHER = "other"

    CHOICES = (
        (PHOTOGRAPH, "Student Photograph"),
        (SYNOPSIS, "Synopsis"),
        (REPORT, "Project Report"),
        (UML, "UML Diagram"),
        (RESEARCH_PAPER, "Research Paper"),
        (CERTIFICATE, "Certificate"),
        (COMPETITION_CERT, "Competition Certificate"),
        (SPONSORSHIP_LETTER, "Sponsorship Letter"),
        (COMPLETION_LETTER, "Completion Letter"),
        (PPT, "PPT"),
        (SOURCE_CODE, "Source Code"),
        (OTHER, "Other"),
    )


class DocumentStatus:
    UPLOADED = "uploaded"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"

    CHOICES = (
        (UPLOADED, "Uploaded"),
        (APPROVED, "Approved"),
        (REJECTED, "Rejected"),
        (ARCHIVED, "Archived"),
    )


class Document(models.Model):
    group = models.ForeignKey(
        "groups.ProjectGroup", on_delete=models.CASCADE, related_name="documents"
    )
    doc_type = models.CharField(max_length=50, choices=DocumentType.CHOICES)
    title = models.CharField(max_length=500)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="uploaded_documents",
    )
    stage = models.ForeignKey(
        "projects.ProjectStage",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="documents",
    )
    file_path = models.CharField(max_length=500)
    file_size = models.BigIntegerField(null=True, blank=True)
    mime_type = models.CharField(max_length=200, blank=True)
    status = models.CharField(
        max_length=20, choices=DocumentStatus.CHOICES, default=DocumentStatus.UPLOADED
    )
    remarks = models.TextField(blank=True)
    current_version = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "document"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.doc_type}) - Group {self.group.group_number}"


class DocumentVersion(models.Model):
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name="versions"
    )
    version_number = models.IntegerField()
    file_path = models.CharField(max_length=500)
    file_size = models.BigIntegerField()
    mime_type = models.CharField(max_length=200, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(default=timezone.now)
    remarks = models.TextField(blank=True)

    class Meta:
        db_table = "document_version"
        unique_together = ["document", "version_number"]
        ordering = ["version_number"]

    def __str__(self):
        return f"v{self.version_number} - {self.document.title}"
