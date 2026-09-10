from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone


class User(AbstractUser):
    ROLE_CHOICES = (
        ("student", "Student"),
        ("faculty", "Faculty"),
        ("reviewer", "Reviewer"),
        ("hod", "HOD"),
        ("admin", "Admin"),
    )

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="student")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "auth_user"
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.email} ({self.role})"

    @property
    def full_name(self):
        return (
            f"{self.first_name} {self.last_name}" if self.first_name else self.username
        )


class StudentProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )
    roll_number = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    mobile = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    exam_seat_number = models.CharField(max_length=50, blank=True)
    department = models.CharField(max_length=200, blank=True)
    enrollment_year = models.IntegerField(blank=True, null=True)
    academic_year = models.ForeignKey(
        "academics.AcademicYear", on_delete=models.CASCADE, null=True, blank=True
    )
    photograph = models.ImageField(upload_to="students/photos/", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "student_profile"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.roll_number})"


class FacultyProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="faculty_profile",
    )
    employee_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    designation = models.CharField(max_length=100)
    specialization = models.CharField(max_length=200, blank=True)
    department = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "faculty_profile"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.employee_id})"
