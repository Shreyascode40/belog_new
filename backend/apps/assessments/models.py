from django.db import models
from django.utils import timezone


class Assessment(models.Model):
    group = models.ForeignKey(
        "groups.ProjectGroup", on_delete=models.CASCADE, related_name="assessments"
    )
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    max_marks = models.DecimalField(max_digits=6, decimal_places=2, default=100)
    obtained_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "assessment"

    def __str__(self):
        return self.title
