'''
Created on Aug 10, 2016

@author: lubo
'''
from django.contrib.auth import get_user_model
from django.contrib.auth.models import BaseUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.response import Response

from models import VerificationPath
from serializers import UserSerializer


# from django.contrib.auth.models import AnonymousUser
@receiver(post_save, sender=get_user_model())
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


@api_view(['POST'])
def register(request):
    serialized = UserSerializer(data=request.data)
    if serialized.is_valid():
        user = get_user_model()
        researcher_id = serialized.validated_data['researcher_id']
        email = BaseUserManager.normalize_email(
            serialized.validated_data['email'])

        created_user = user.objects.create_user(email, researcher_id)
        created_user.first_name = serialized.validated_data['first_name']
        created_user.last_name = serialized.validated_data['last_name']

        created_user.save()
        return Response(serialized.data, status=status.HTTP_201_CREATED)
    else:
        return Response(serialized._errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def check_verif_path(request):
    verif_path = request.data['verif_path']
    try:
        VerificationPath.objects.get(path=verif_path)
        return Response({}, status=status.HTTP_200_OK)
    except VerificationPath.DoesNotExist:
        return Response({
            'errors': 'Verification path does not exist.'},
            status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def change_password(request):
    password = request.data['password']
    verif_path = request.data['verif_path']

    user = get_user_model().change_password(verif_path, password)

    return Response({'username': user.email, 'password': password},
                    status.HTTP_201_CREATED)


@api_view(['POST'])
def get_user_info(request):
    token = request.data['token']
    try:
        user = Token.objects.get(key=token).user
        if (user.is_staff):
            userType = 'admin'
        else:
            userType = 'registered'

        return Response({'userType': userType,
                         'email': user.email}, status.HTTP_200_OK)
    except Token.DoesNotExist:
        return Response({}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def reset_password(request):
    email = request.data['email']
    user_model = get_user_model()
    try:
        user = user_model.objects.get(email=email)
        user.reset_password()

        return Response({}, status.HTTP_200_OK)
    except user_model.DoesNotExist:
        return Response({'errors': 'User with this email not found'},
                        status=status.HTTP_400_BAD_REQUEST)
