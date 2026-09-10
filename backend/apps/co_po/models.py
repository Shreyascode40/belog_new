from django.db import models
from django.conf import settings
from django.utils import timezone


class CO(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    department = models.ForeignKey(
        "academics.Department", on_delete=models.CASCADE, related_name="cos"
    )
    academic_year = models.ForeignKey(
        "academics.AcademicYear", on_delete=models.CASCADE, related_name="cos"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "co"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name[:50]}"


class PO(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    department = models.ForeignKey(
        "academics.Department", on_delete=models.CASCADE, related_name="pos"
    )
    academic_year = models.ForeignKey(
        "academics.AcademicYear", on_delete=models.CASCADE, related_name="pos"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "po"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name[:50]}"


class COPOMapping(models.Model):
    co = models.ForeignKey(CO, on_delete=models.CASCADE, related_name="po_mappings")
    po = models.ForeignKey(PO, on_delete=models.CASCADE, related_name="co_mappings")
    weightage = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        db_table = "co_po_mapping"
        unique_together = ["co", "po"]

    def __str__(self):
        return f"{self.co.code} → {self.po.code}"


class COAttainment(models.Model):
    co = models.ForeignKey(CO, on_delete=models.CASCADE, related_name="attainments")
    group = models.ForeignKey(
        "groups.ProjectGroup", on_delete=models.CASCADE, related_name="co_attainments"
    )
    review = models.ForeignKey(
        "reviews.Review",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="co_attainments",
    )
    raw_marks = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    max_marks = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    normalized_marks = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    attainment_level = models.CharField(max_length=50, blank=True)
    calculated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "co_attainment"
        unique_together = ["co", "group", "review"]

    def __str__(self):
        return f"{self.co.code} - Group {self.group.group_number}"


class POAttainment(models.Model):
    po = models.ForeignKey(PO, on_delete=models.CASCADE, related_name="po_attainments")
    group = models.ForeignKey(
        "groups.ProjectGroup", on_delete=models.CASCADE, related_name="po_attainments"
    )
    normalized_marks = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    attainment_level = models.CharField(max_length=50, blank=True)
    calculated_at = models.DateTimeField(default=timezone.now)
    review = models.ForeignKey(
        "reviews.Review",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="po_attainments",
    )

    class Meta:
        db_table = "po_attainment"
        unique_together = ["po", "group", "review"]

    def __str__(self):
        return f"{self.po.code} - Group {self.group.group_number}"
