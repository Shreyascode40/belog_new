from rest_framework import serializers
from .models import AccessGrant


class AccessGrantSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessGrant
        fields = "__all__"
        read_only_fields = [
            "granted_by",
            "granted_at",
            "revoked_at",
            "created_at",
            "updated_at",
        ]
