
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Review, ReviewCriterion, Mark, Approval
from .serializers import ReviewSerializer, ReviewCriterionSerializer, MarkSerializer, ApprovalSerializer
class ReviewViewSet(viewsets.ModelViewSet):
    queryset=Review.objects.all()
    serializer_class=ReviewSerializer
    @action(detail=True, methods=['post'])
    def finalize(self, request, pk=None):
        r=self.get_object()
        if r.criteria.count()==0:
            return Response({'success':False,'message':'No criteria'},status=400)
        r.status='finalized'
        r.finalized_at=timezone.now()
        r.finalized_by=request.user
        r.save()
        return Response(ReviewSerializer(r).data)
class ReviewCriterionViewSet(viewsets.ModelViewSet):
    queryset=ReviewCriterion.objects.all()
    serializer_class=ReviewCriterionSerializer
class MarkViewSet(viewsets.ModelViewSet):
    queryset=Mark.objects.all()
    serializer_class=MarkSerializer
class ApprovalViewSet(viewsets.ModelViewSet):
    queryset=Approval.objects.all()
    serializer_class=ApprovalSerializer
