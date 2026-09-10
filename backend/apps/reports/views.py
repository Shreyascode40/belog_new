from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Report
from .serializers import ReportSerializer
from apps.groups.models import ProjectGroup
class ReportViewSet(viewsets.ModelViewSet):
    queryset=Report.objects.all()
    serializer_class=ReportSerializer
@api_view(['GET'])
def dashboard_hod(request):
    total=ProjectGroup.objects.count()
    completed=ProjectGroup.objects.filter(status='completed').count()
    active=ProjectGroup.objects.filter(status='active').count()
    return Response({'success':True,'data':{'total_groups':total,'completed':completed,'in_progress':active}})
@api_view(['GET'])
def dashboard_student(request):
    groups=ProjectGroup.objects.filter(members__student=request.user)
    g=groups.first()
    prog=g.progress if g else 0
    return Response({'success':True,'data':{'my_group': list(groups.values('id','group_number')), 'progress':prog}})
@api_view(['GET'])
def dashboard_faculty(request):
    from apps.groups.models import ProjectGuideAssignment
    assigned=ProjectGuideAssignment.objects.filter(faculty=request.user).count()
    return Response({'success':True,'data':{'assigned_groups':assigned}})
