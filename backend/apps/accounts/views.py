
from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .models import StudentProfile, FacultyProfile
from .serializers import UserSerializer, RegisterSerializer, LoginSerializer, StudentProfileSerializer, FacultyProfileSerializer
from apps.common.permissions import IsHOD
User=get_user_model()
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    s=RegisterSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    u=s.save()
    r=RefreshToken.for_user(u)
    return Response({'success':True,'data':UserSerializer(u).data,'tokens':{'refresh':str(r),'access':str(r.access_token)}},status=201)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    s=LoginSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    try:
        u=User.objects.get(email=s.validated_data['email'])
    except User.DoesNotExist:
        return Response({'success':False,'message':'Invalid credentials'},status=401)
    if not u.check_password(s.validated_data['password']):
        return Response({'success':False,'message':'Invalid credentials'},status=401)
    if not u.is_active:
        return Response({'success':False,'message':'Account deactivated'},status=403)
    r=RefreshToken.for_user(u)
    return Response({'success':True,'data':UserSerializer(u).data,'tokens':{'refresh':str(r),'access':str(r.access_token)}})
@api_view(['GET'])
def me(request):
    return Response({'success':True,'data':UserSerializer(request.user).data})
class UserViewSet(viewsets.ModelViewSet):
    queryset=User.objects.all().order_by('-date_joined')
    serializer_class=UserSerializer
    def get_permissions(self):
        if self.action in ['list','create','destroy','update','partial_update']:
            return [IsHOD()]
        return [permissions.IsAuthenticated()]
class StudentProfileViewSet(viewsets.ModelViewSet):
    queryset=StudentProfile.objects.all()
    serializer_class=StudentProfileSerializer
class FacultyProfileViewSet(viewsets.ModelViewSet):
    queryset=FacultyProfile.objects.all()
    serializer_class=FacultyProfileSerializer
