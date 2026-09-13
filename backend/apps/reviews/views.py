from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Review, ReviewCriterion, Mark, Approval
from .serializers import (
    ReviewSerializer,
    ReviewCriterionSerializer,
    MarkSerializer,
    ApprovalSerializer,
)


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        qs = Review.objects.all()
        u = self.request.user
        if u and u.role == "student":
            return qs.filter(
                group__members__student=u, group__members__status="accepted"
            ).distinct()
        if u and u.role in ["faculty", "reviewer"]:
            return (
                qs.filter(group__guide_assignments__faculty=u).distinct()
                | qs.filter(group__reviewer_assignments__faculty=u).distinct()
            )
        return qs

    @action(detail=True, methods=["post"])
    def finalize(self, request, pk=None):
        r = self.get_object()
        if r.criteria.count() == 0:
            return Response({"success": False, "message": "No criteria"}, status=400)
        r.status = "finalized"
        r.finalized_at = timezone.now()
        r.finalized_by = request.user
        r.save()
        return Response(ReviewSerializer(r).data)


class ReviewCriterionViewSet(viewsets.ModelViewSet):
    queryset = ReviewCriterion.objects.all()
    serializer_class = ReviewCriterionSerializer

    def get_queryset(self):
        qs = ReviewCriterion.objects.all()
        u = self.request.user
        if u and u.role == "student":
            return qs.filter(review__group__members__student=u).distinct()
        return qs


class MarkViewSet(viewsets.ModelViewSet):
    serializer_class = MarkSerializer

    def get_queryset(self):
        qs = Mark.objects.all()
        u = self.request.user
        if u and u.role == "student":
            return qs.filter(group__members__student=u, is_finalized=True).distinct()
        return qs


class ApprovalViewSet(viewsets.ModelViewSet):
    serializer_class = ApprovalSerializer

    def get_queryset(self):
        qs = Approval.objects.all()
        u = self.request.user
        if u and u.role == "student":
            return qs.filter(submission__group__members__student=u).distinct()
        return qs
