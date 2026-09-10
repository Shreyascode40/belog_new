from rest_framework import viewsets
from .models import AuditLog, Deadline
from .serializers import AuditLogSerializer, DeadlineSerializer
from apps.common.permissions import IsHOD
class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset=AuditLog.objects.all()
    serializer_class=AuditLogSerializer
    permission_classes=[IsHOD]
class DeadlineViewSet(viewsets.ModelViewSet):
    queryset=Deadline.objects.all()
    serializer_class=DeadlineSerializer
