from rest_framework import serializers
from .models import AuditLog, Deadline
class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model=AuditLog
        fields='__all__'
class DeadlineSerializer(serializers.ModelSerializer):
    class Meta:
        model=Deadline
        fields='__all__'
