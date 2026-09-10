
from rest_framework import serializers
from .models import Document, DocumentVersion
class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model=Document
        fields='__all__'
class DocumentVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model=DocumentVersion
        fields='__all__'
