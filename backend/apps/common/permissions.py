from rest_framework.permissions import BasePermission


class IsHOD(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ["hod", "admin"]
        )


class IsFaculty(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ["faculty", "reviewer", "hod", "admin"]
        )


class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "student"
        )


class IsOwnerOrHOD(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role in ["hod", "admin"]:
            return True
        if hasattr(obj, "user"):
            return obj.user == request.user
        if hasattr(obj, "student"):
            return obj.student == request.user
        return False
