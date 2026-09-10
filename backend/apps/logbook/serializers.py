from rest_framework import serializers
from .models import FinalLogBook, HODFinalApproval


class FinalLogBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinalLogBook
        fields = "__all__"


class HODFinalApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = HODFinalApproval
        fields = "__all__"
