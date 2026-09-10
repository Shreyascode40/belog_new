from rest_framework import serializers
from .models import (
    ProjectGroup,
    GroupMember,
    ProjectGuideAssignment,
    ReviewerAssignment,
)


class GroupMemberSerializer(serializers.ModelSerializer):
    student_detail = serializers.SerializerMethodField(read_only=True)

    def get_student_detail(self, obj):
        try:
            p = obj.student.student_profile
            return {
                "id": p.id,
                "user_id": obj.student.id,
                "name": p.name,
                "roll_number": p.roll_number,
                "mobile": p.mobile,
                "exam_seat_number": p.exam_seat_number,
                "email": p.email or obj.student.email,
                "department": p.department,
            }
        except:
            return {
                "id": None,
                "user_id": obj.student.id,
                "name": obj.student.username,
                "email": obj.student.email,
                "roll_number": "",
                "mobile": "",
                "exam_seat_number": "",
            }

    class Meta:
        model = GroupMember
        fields = "__all__"


class ProjectGroupSerializer(serializers.ModelSerializer):
    members = GroupMemberSerializer(many=True, read_only=True)
    progress = serializers.ReadOnlyField()
    project_title = serializers.CharField(write_only=True, required=False)
    area = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = ProjectGroup
        fields = "__all__"
        read_only_fields = [
            "group_number",
            "academic_year",
            "department",
            "project",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        validated_data.pop("project_title", None)
        validated_data.pop("area", None)
        return super().create(validated_data)


class GuideAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectGuideAssignment
        fields = "__all__"


class ReviewerAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewerAssignment
        fields = "__all__"
