from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Notification
from .serializers import NotificationSerializer
class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class=NotificationSerializer
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')
    @action(detail=True, methods=['post'])
    def read(self, request, pk=None):
        n=self.get_object()
        n.is_read=True
        n.read_at=timezone.now()
        n.save()
        return Response(NotificationSerializer(n).data)
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True, read_at=timezone.now())
        return Response({'success':True})
