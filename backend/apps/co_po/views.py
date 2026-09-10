from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import CO, PO, COPOMapping, COAttainment, POAttainment
from .serializers import COSerializer, POSerializer, COPOMappingSerializer, COAttainmentSerializer, POAttainmentSerializer
class COViewSet(viewsets.ModelViewSet):
    queryset=CO.objects.all()
    serializer_class=COSerializer
class POViewSet(viewsets.ModelViewSet):
    queryset=PO.objects.all()
    serializer_class=POSerializer
class COPOMappingViewSet(viewsets.ModelViewSet):
    queryset=COPOMapping.objects.all()
    serializer_class=COPOMappingSerializer
class COAttainmentViewSet(viewsets.ModelViewSet):
    queryset=COAttainment.objects.all()
    serializer_class=COAttainmentSerializer
class POAttainmentViewSet(viewsets.ModelViewSet):
    queryset=POAttainment.objects.all()
    serializer_class=POAttainmentSerializer
@api_view(['POST'])
def calculate_attainment(request):
    gid=request.data.get('group_id')
    from apps.reviews.models import Mark
    results=[]
    for co in CO.objects.all():
        marks=Mark.objects.filter(criterion__co=co, group_id=gid, status='finalized')
        raw=sum(float(m.obtained_marks) for m in marks)
        maxm=sum(float(m.criterion.max_marks) for m in marks)
        norm=round(raw/maxm*100,2) if maxm else 0
        if norm>=90: lvl='EXCELLENT'
        elif norm>=80: lvl='GOOD'
        elif norm>=70: lvl='SATISFACTORY'
        elif norm>=60: lvl='NEEDS_IMPROVEMENT'
        else: lvl='UNSATISFACTORY'
        obj,_=COAttainment.objects.update_or_create(co=co, group_id=gid, defaults={'raw_marks':raw,'max_marks':maxm,'normalized_marks':norm,'attainment_level':lvl})
        results.append(COAttainmentSerializer(obj).data)
    return Response({'success':True,'data':results})
