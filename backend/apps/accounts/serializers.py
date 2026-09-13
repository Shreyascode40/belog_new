from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import StudentProfile, FacultyProfile

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_active",
            "date_joined",
        ]
        read_only_fields = ["id", "date_joined"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    role = serializers.ChoiceField(
        choices=[
            ("student", "Student"),
            ("faculty", "Faculty"),
            ("hod", "HOD"),
            ("reviewer", "Reviewer"),
        ],
        required=False,
        default="student",
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "role",
        ]
        read_only_fields = ["id"]

    def validate_email(self, v):
        em = v.strip().lower()
        if not em or "@" not in em:
            raise serializers.ValidationError("Enter a valid email")
        if User.objects.filter(email__iexact=em).exists():
            raise serializers.ValidationError("Email already registered — try Login")
        return em

    def validate_username(self, v):
        if not v:
            return v
        u = v.strip()
        if len(u) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters")
        return u

    def create(self, v):
        email = v["email"].strip().lower()
        username = v.get("username", "").strip() or email.split("@")[0]
        base = username
        i = 0
        while User.objects.filter(username__iexact=username).exists():
            i += 1
            username = f"{base}{i}"
        return User.objects.create_user(
            username=username,
            email=email,
            password=v["password"],
            first_name=v.get("first_name", ""),
            last_name=v.get("last_name", ""),
            role=v.get("role", "student"),
        )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate_email(self, v):
        return v.strip().lower()


class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = "__all__"


class FacultyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacultyProfile
        fields = "__all__"
