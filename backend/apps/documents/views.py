from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from .models import Document, DocumentVersion
from .serializers import DocumentSerializer, DocumentVersionSerializer


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer

    def get_queryset(self):
        qs = Document.objects.all()
        u = self.request.user
        if u and u.is_authenticated and u.role == "student":
            return qs.filter(
                group__members__student=u, group__members__status="accepted"
            ).distinct()
        if u and u.role in ["faculty", "reviewer"]:
            return (
                qs.filter(group__guide_assignments__faculty=u).distinct()
                | qs.filter(group__reviewer_assignments__faculty=u).distinct()
                | qs.filter(group__members__student=u).distinct()
            )
        return qs

    def perform_create(self, serializer):
        group = serializer.validated_data.get("group")
        u = self.request.user
        if (
            u.role == "student"
            and not group.members.filter(student=u, status="accepted").exists()
        ):
            raise PermissionDenied("Not your group")
        serializer.save()


class DocumentVersionViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentVersionSerializer

    def get_queryset(self):
        qs = DocumentVersion.objects.all()
        u = self.request.user
        if u and u.role == "student":
            return qs.filter(document__group__members__student=u).distinct()
        return qs
