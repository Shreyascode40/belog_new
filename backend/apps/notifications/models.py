from django.db import models
from django.conf import settings
from django.utils import timezone


class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    notification_type = models.CharField(
        max_length=30,
        choices=[
            ("approval", "Approval"),
            ("change_request", "Change Request"),
            ("deadline", "Deadline"),
            ("pending_action", "Pending Action"),
            ("overdue", "Overdue"),
            ("submission", "Submission"),
            ("milestone", "Milestone"),
            ("system", "System"),
        ],
    )
    title = models.CharField(max_length=300)
    message = models.TextField()
    related_type = models.CharField(max_length=50, blank=True)
    related_id = models.BigIntegerField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "notification"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} -> {self.recipient.email}"
