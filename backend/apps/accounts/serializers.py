
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import StudentProfile, FacultyProfile
User=get_user_model()
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields=['id','username','email','first_name','last_name','role','is_active','date_joined']
        read_only_fields=['id','date_joined']
class RegisterSerializer(serializers.ModelSerializer):
    password=serializers.CharField(write_only=True, min_length=6)
    class Meta:
        model=User
        fields=['id','username','email','password','first_name','last_name','role']
        read_only_fields=['id']
    def create(self, v):
        return User.objects.create_user(username=v['username'],email=v['email'],password=v['password'],first_name=v.get('first_name',''),last_name=v.get('last_name',''),role=v.get('role','student'))
class LoginSerializer(serializers.Serializer):
    email=serializers.EmailField()
    password=serializers.CharField()
class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model=StudentProfile
        fields='__all__'
class FacultyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model=FacultyProfile
        fields='__all__'
