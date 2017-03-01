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
import django.contrib.auth
from django.views.decorators.csrf import csrf_exempt
from authentication import DpfSessionAuthentication
from rest_framework.decorators import authentication_classes
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from models import VerificationPath
from serializers import UserSerializer


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
def login(request):
    username = request.data['username']
    password = request.data['password']
    user = django.contrib.auth.authenticate(username=username, password=password)
    if user is not None and user.is_active:
        django.contrib.auth.login(request, user)
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@authentication_classes((DpfSessionAuthentication, BasicAuthentication))
def logout(request):
    django.contrib.auth.logout(request)
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def get_user_info(request):
    user = request.user
    if user.is_authenticated():
        return Response({'loggedIn': True, 'email': user.email}, status.HTTP_200_OK)
    else:
        return Response({'loggedIn': False}, status.HTTP_200_OK)
