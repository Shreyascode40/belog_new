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
        except Exception:
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
        read_only_fields = ["joined_date", "acknowledged", "acknowledged_at"]


class GroupMemberWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    roll_number = serializers.CharField(max_length=50)
    email = serializers.EmailField()
    role = serializers.ChoiceField(
        choices=[("leader", "Leader"), ("member", "Member")],
        required=False,
        default="member",
    )


class GuideDetailSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()

    def get_name(self, obj):
        try:
            return obj.faculty.faculty_profile.name
        except Exception:
            return obj.faculty.get_full_name() or obj.faculty.username

    def get_email(self, obj):
        return obj.faculty.email

    class Meta:
        model = ProjectGuideAssignment
        fields = ["id", "faculty", "name", "email", "assigned_date", "is_active"]


class ProjectDetailSerializer(serializers.Serializer):
    title = serializers.CharField()
    area_domain = serializers.CharField()
    description = serializers.CharField(allow_blank=True, required=False)


class GroupProfileSerializer(serializers.ModelSerializer):
    members = GroupMemberSerializer(many=True, read_only=True)
    progress = serializers.ReadOnlyField()
    is_locked = serializers.ReadOnlyField()
    semester = serializers.SerializerMethodField()
    academic_year_detail = serializers.SerializerMethodField()
    department_detail = serializers.SerializerMethodField()
    project_detail = serializers.SerializerMethodField()
    guide_detail = serializers.SerializerMethodField()
    group_members_config = serializers.SerializerMethodField()
    updated_by_email = serializers.SerializerMethodField()

    def get_semester(self, obj):
        s = obj.semester
        if not s:
            return None
        return {"id": s.id, "name": s.name, "number": s.number}

    def get_academic_year_detail(self, obj):
        try:
            ay = obj.academic_year
            return {
                "id": ay.id,
                "year_label": ay.year_label,
                "start_date": ay.start_date,
                "end_date": ay.end_date,
                "is_current": ay.is_current,
            }
        except Exception:
            return None

    def get_department_detail(self, obj):
        try:
            d = obj.department
            return {"id": d.id, "name": d.name, "code": d.code}
        except Exception:
            return None

    def get_project_detail(self, obj):
        try:
            p = obj.project
            if not p:
                return None
            return {
                "id": p.id,
                "title": p.title,
                "area_domain": p.area_domain,
                "description": p.description,
                "technology_stack": p.technology_stack,
            }
        except Exception:
            return None

    def get_guide_detail(self, obj):
        ga = obj.guide_assignments.filter(is_active=True).first()
        if not ga:
            return None
        try:
            prof = ga.faculty.faculty_profile
            return {
                "id": ga.faculty.id,
                "name": prof.name,
                "email": ga.faculty.email,
                "designation": prof.designation,
                "department": prof.department,
            }
        except Exception:
            return {
                "id": ga.faculty.id,
                "name": ga.faculty.username,
                "email": ga.faculty.email,
                "designation": "",
                "department": "",
            }

    def get_group_members_config(self, obj):
        from django.conf import settings

        return {
            "min": int(getattr(settings, "GROUP_MIN_SIZE", 2)),
            "max": int(getattr(settings, "GROUP_MAX_SIZE", 4)),
            "current": obj.members.filter(status="accepted", is_active=True).count(),
        }

    def get_updated_by_email(self, obj):
        return obj.updated_by.email if obj.updated_by else None

    class Meta:
        model = ProjectGroup
        fields = [
            "id",
            "group_number",
            "academic_year",
            "academic_year_detail",
            "department",
            "department_detail",
            "semester",
            "project",
            "project_detail",
            "guide_detail",
            "status",
            "is_locked",
            "progress",
            "members",
            "group_members_config",
            "created_at",
            "updated_at",
            "updated_by",
            "updated_by_email",
            "is_active",
        ]
        read_only_fields = [
            "id",
            "group_number",
            "academic_year",
            "department",
            "project",
            "status",
            "progress",
            "is_locked",
            "created_at",
            "updated_at",
            "updated_by",
        ]


class ProjectGroupSerializer(serializers.ModelSerializer):
    members = GroupMemberSerializer(many=True, read_only=True)
    progress = serializers.ReadOnlyField()
    project_detail = serializers.SerializerMethodField(read_only=True)
    project_title = serializers.CharField(write_only=True, required=False)
    area = serializers.CharField(write_only=True, required=False)

    def get_project_detail(self, obj):
        try:
            p = obj.project
            if not p:
                return None
            return {
                "id": p.id,
                "title": p.title,
                "area_domain": p.area_domain,
                "description": p.description,
            }
        except Exception:
            return None

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
            "updated_by",
        ]

    def create(self, validated_data):
        validated_data.pop("project_title", None)
        validated_data.pop("area", None)
        return super().create(validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data.get("project_detail"):
            data["project"] = data["project_detail"]
        return data


class GuideAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectGuideAssignment
        fields = "__all__"


class ReviewerAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewerAssignment
        fields = "__all__"
