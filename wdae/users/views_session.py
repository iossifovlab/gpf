'''
Created on Aug 10, 2016

@author: lubo
'''
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import BaseUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.response import Response
import django.contrib.auth
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from authentication import SessionAuthenticationWithUnauthenticatedCSRF, SessionAuthenticationWithoutCSRF
from rest_framework.decorators import authentication_classes
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from models import VerificationPath
from serializers_session import UserSerializer


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

@api_view(['POST'])
def change_password(request):
    password = request.data['password']
    verif_path = request.data['verifPath']

    user = get_user_model().change_password(verif_path, password)

    return Response({}, status.HTTP_201_CREATED)

@api_view(['POST'])
def register(request):
    serialized = UserSerializer(data=request.data)
    if serialized.is_valid():
        user = get_user_model()
        researcher_id = serialized.validated_data['researcherId']
        email = BaseUserManager.normalize_email(
            serialized.validated_data['email'])

        created_user = user.objects.get(email=email)
        try:
            created_user.register_preexisting_user(
                serialized.validated_data['firstName'],
                serialized.validated_data['lastName']
            )
            return Response(serialized.data, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response(serialized._errors,
                status=status.HTTP_400_BAD_REQUEST)

    else:
        return Response(serialized._errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@authentication_classes((SessionAuthenticationWithUnauthenticatedCSRF, ))
def login(request):
    username = request.data['username']
    password = request.data['password']
    user = django.contrib.auth.authenticate(username=username, password=password)
    if user is not None and user.is_active:
        django.contrib.auth.login(request, user)
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@authentication_classes((SessionAuthentication, ))
def logout(request):
    django.contrib.auth.logout(request)
    return Response(status=status.HTTP_204_NO_CONTENT)


@ensure_csrf_cookie
@api_view(['GET'])
def get_user_info(request):
    user = request.user
    if user.is_authenticated():
        return Response({'loggedIn': True, 'email': user.email}, status.HTTP_200_OK)
    else:
        return Response({'loggedIn': False}, status.HTTP_200_OK)

@api_view(['POST'])
def check_verif_path(request):
    verif_path = request.data['verifPath']
    try:
        VerificationPath.objects.get(path=verif_path)
        return Response({}, status=status.HTTP_200_OK)
    except VerificationPath.DoesNotExist:
        return Response({
            'errors': 'Verification path does not exist.'},
            status=status.HTTP_400_BAD_REQUEST)
