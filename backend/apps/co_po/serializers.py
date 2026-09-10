
from rest_framework import serializers
from .models import CO, PO, COPOMapping, COAttainment, POAttainment
class COSerializer(serializers.ModelSerializer):
    class Meta:
        model=CO
        fields='__all__'
class POSerializer(serializers.ModelSerializer):
    class Meta:
        model=PO
        fields='__all__'
class COPOMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model=COPOMapping
        fields='__all__'
class COAttainmentSerializer(serializers.ModelSerializer):
    class Meta:
        model=COAttainment
        fields='__all__'
class POAttainmentSerializer(serializers.ModelSerializer):
    class Meta:
        model=POAttainment
        fields='__all__'
