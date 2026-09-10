
from rest_framework import serializers
from .models import Review, ReviewCriterion, Mark, Approval
class ReviewCriterionSerializer(serializers.ModelSerializer):
    class Meta:
        model=ReviewCriterion
        fields='__all__'
class MarkSerializer(serializers.ModelSerializer):
    class Meta:
        model=Mark
        fields='__all__'
    def validate(self, data):
        crit=data.get('criterion') or (self.instance.criterion if self.instance else None)
        marks=data.get('obtained_marks')
        if crit and marks is not None:
            if marks < 0:
                raise serializers.ValidationError({'obtained_marks':'Cannot be negative'})
            if float(marks) > float(crit.max_marks):
                raise serializers.ValidationError({'obtained_marks':'Exceeds max marks'})
        return data
class ReviewSerializer(serializers.ModelSerializer):
    criteria=ReviewCriterionSerializer(many=True, read_only=True)
    class Meta:
        model=Review
        fields='__all__'
class ApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model=Approval
        fields='__all__'
