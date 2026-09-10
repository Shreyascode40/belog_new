from django.db import models
from django.conf import settings
from django.utils import timezone


class AccessGrant(models.Model):
    group = models.ForeignKey(
        "groups.ProjectGroup", on_delete=models.CASCADE, related_name="access_grants"
    )
    stage = models.ForeignKey(
        "projects.ProjectStage", on_delete=models.CASCADE, related_name="access_grants"
    )
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="access_grants_given",
    )
    granted = models.BooleanField(default=False)
    remark = models.TextField(blank=True)
    granted_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "access_grant"
        unique_together = ["group", "stage"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"AccessGrant group {self.group_id} stage {self.stage_id} granted={self.granted}"
