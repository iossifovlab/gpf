'''
Created on Aug 10, 2016

@author: lubo
'''
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import BaseUserManager
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
import django.contrib.auth
from rest_framework.decorators import authentication_classes
from models import VerificationPath
from rest_framework.authentication import SessionAuthentication
from users_api.authentication import \
    SessionAuthenticationWithUnauthenticatedCSRF
from django.views.decorators.csrf import ensure_csrf_cookie


@api_view(['POST'])
def reset_password(request):
    email = request.data['email']
    user_model = get_user_model()
    try:
        user = user_model.objects.get(email=email, is_active=True)
        user.reset_password()

        return Response({}, status.HTTP_200_OK)
    except user_model.DoesNotExist:
        return Response({'errors': 'User with this email not found'},
                        status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def change_password(request):
    password = request.data['password']
    verif_path = request.data['verifPath']

    get_user_model().change_password(verif_path, password)

    return Response({}, status.HTTP_201_CREATED)


@api_view(['POST'])
def register(request):
    user_model = get_user_model()

    try:
        email = BaseUserManager.normalize_email(request.data['email'])
        researcher_id = request.data['researcherId']
        group_name = user_model.get_group_name_for_researcher_id(researcher_id)

        preexisting_user = user_model.objects.get(email=email,
                                                  groups__name=group_name)
        if preexisting_user.is_active:
            return Response({'error_msg': 'User already exists'},
                            status=status.HTTP_409_CONFLICT)

        preexisting_user.register_preexisting_user(request.data['name'])
        return Response({}, status=status.HTTP_201_CREATED)
    except IntegrityError:
        return Response({}, status=status.HTTP_400_BAD_REQUEST)
    except user_model.DoesNotExist:
        return Response({'error_msg': 'Email or Researcher Id not found'},
                        status=status.HTTP_404_NOT_FOUND)
    except KeyError:
        return Response({}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@authentication_classes((SessionAuthenticationWithUnauthenticatedCSRF, ))
def login(request):
    username = request.data['username']
    password = request.data['password']
    user = django.contrib.auth.authenticate(username=username,
                                            password=password)
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
        return Response({'loggedIn': True, 'email': user.email},
                        status.HTTP_200_OK)
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
