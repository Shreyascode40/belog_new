from django.db import models
from django.conf import settings
from django.utils import timezone


class Department(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "department"
        ordering = ["name"]

    def __str__(self):
        return self.name


class AcademicYear(models.Model):
    year_label = models.CharField(max_length=20, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="academic_years"
    )
    is_current = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "academic_year"
        ordering = ["-start_date"]

    def __str__(self):
        return self.year_label


class Semester(models.Model):
    name = models.CharField(max_length=100)
    academic_year = models.ForeignKey(
        AcademicYear, on_delete=models.CASCADE, related_name="semesters"
    )
    number = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "semester"
        ordering = ["academic_year", "number"]
        unique_together = ["academic_year", "number"]

    def __str__(self):
        return f"{self.name} - {self.academic_year.year_label}"
