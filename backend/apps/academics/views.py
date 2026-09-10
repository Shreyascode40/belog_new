
from rest_framework import viewsets
from .models import Department, AcademicYear, Semester
from .serializers import DepartmentSerializer, AcademicYearSerializer, SemesterSerializer
class DepartmentViewSet(viewsets.ModelViewSet):
    queryset=Department.objects.all()
    serializer_class=DepartmentSerializer
class AcademicYearViewSet(viewsets.ModelViewSet):
    queryset=AcademicYear.objects.all()
    serializer_class=AcademicYearSerializer
class SemesterViewSet(viewsets.ModelViewSet):
    queryset=Semester.objects.all()
    serializer_class=SemesterSerializer
