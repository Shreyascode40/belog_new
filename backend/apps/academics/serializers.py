
from rest_framework import serializers
from .models import Department, AcademicYear, Semester
class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model=Department
        fields='__all__'
class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model=AcademicYear
        fields='__all__'
class SemesterSerializer(serializers.ModelSerializer):
    class Meta:
        model=Semester
        fields='__all__'
