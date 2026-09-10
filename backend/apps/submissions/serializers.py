
from rest_framework import serializers
from .models import Submission, SubmissionVersion
class SubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model=Submission
        fields='__all__'
class SubmissionVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model=SubmissionVersion
        fields='__all__'
