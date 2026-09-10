
from rest_framework import serializers
from .models import Project, ProjectStage, StageDependency, Section, Activity
class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model=Project
        fields='__all__'
class ProjectStageSerializer(serializers.ModelSerializer):
    class Meta:
        model=ProjectStage
        fields='__all__'
class StageDependencySerializer(serializers.ModelSerializer):
    class Meta:
        model=StageDependency
        fields='__all__'
class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model=Section
        fields='__all__'
class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model=Activity
        fields='__all__'
