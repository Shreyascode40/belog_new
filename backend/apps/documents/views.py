
from rest_framework import viewsets
from .models import Document, DocumentVersion
from .serializers import DocumentSerializer, DocumentVersionSerializer
class DocumentViewSet(viewsets.ModelViewSet):
    queryset=Document.objects.all()
    serializer_class=DocumentSerializer
class DocumentVersionViewSet(viewsets.ModelViewSet):
    queryset=DocumentVersion.objects.all()
    serializer_class=DocumentVersionSerializer
