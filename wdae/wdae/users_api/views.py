from django.db import IntegrityError, transaction
from django.contrib.auth import get_user_model
from django.contrib.auth.models import BaseUserManager, Group
from django.shortcuts import get_object_or_404, get_list_or_404
from django.views.decorators.csrf import ensure_csrf_cookie
import django.contrib.auth

from rest_framework.decorators import action
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.decorators import authentication_classes
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework import permissions
from rest_framework import filters

from .authentication import \
    SessionAuthenticationWithUnauthenticatedCSRF
from .models import VerificationPath
from .serializers import UserSerializer
from .serializers import UserWithoutEmailSerializer
from .serializers import BulkGroupOperationSerializer

from utils.logger import log_filter, LOGGER, request_logging
from utils.logger import request_logging_function_view


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset = get_user_model().objects.all()
    permission_classes = (permissions.IsAdminUser,)
    pagination_class = None
    filter_backends = (filters.SearchFilter,)
    search_fields = ('groups__name', 'email', 'name')

    def get_serializer_class(self):
        serializer_class = self.serializer_class

        if self.action == 'update' or self.action == 'partial_update':
            serializer_class = UserWithoutEmailSerializer

        return serializer_class

    @request_logging(LOGGER)
    @action(detail=True, methods=['post'])
    def password_remove(self, request, pk=None):
        self.check_permissions(request)
        user = get_object_or_404(get_user_model(), pk=pk)

        if user.has_usable_password():
            user.set_unusable_password()
            user.save()
            user.deauthenticate()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @request_logging(LOGGER)
    @action(detail=True, methods=['post'])
    def password_reset(self, request, pk=None):
        self.check_permissions(request)
        user = get_object_or_404(get_user_model(), pk=pk)

        user.reset_password(by_admin=True)
        user.deauthenticate()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @request_logging(LOGGER)
    @action(detail=False, methods=['post'])
    def bulk_add_group(self, request):
        self.check_permissions(request)

        serializer = BulkGroupOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        users = get_list_or_404(get_user_model(), id__in=data['userIds'])
        if len(users) != len(data['userIds']):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            group, _ = Group.objects.get_or_create(name=data['group'])

            group.user_set.add(*users)

        return Response(status=status.HTTP_200_OK)

    @request_logging(LOGGER)
    @action(detail=False, methods=['post'])
    def bulk_remove_group(self, request):
        serializer = BulkGroupOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        users = get_list_or_404(get_user_model(), id__in=data['userIds'])
        if len(users) != len(data['userIds']):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        group = get_object_or_404(Group, name=data['group'])
        with transaction.atomic():
            group.user_set.remove(*users)

        return Response(status=status.HTTP_200_OK)


@request_logging_function_view(LOGGER)
@api_view(['POST'])
def reset_password(request):
    email = request.data['email']
    user_model = get_user_model()
    try:
        user = user_model.objects.get(email=email)
        if not user.is_active:
            return Response({}, status=status.HTTP_200_OK)
        user.reset_password()
        user.deauthenticate()

        return Response({}, status.HTTP_200_OK)
    except user_model.DoesNotExist:
        return Response({},
                        status=status.HTTP_200_OK)


@request_logging_function_view(LOGGER)
@api_view(['POST'])
def change_password(request):
    password = request.data['password']
    verif_path = request.data['verifPath']

    get_user_model().change_password(verif_path, password)

    return Response({}, status.HTTP_201_CREATED)


@request_logging_function_view(LOGGER)
@api_view(['POST'])
def register(request):
    user_model = get_user_model()

    try:
        email = BaseUserManager.normalize_email(request.data['email'])
        researcher_id = request.data['researcherId']
        group_name = user_model.get_group_name_for_researcher_id(researcher_id)

        preexisting_user = user_model.objects.get(email__iexact=email,
                                                  groups__name=group_name)
        if preexisting_user.is_active:
            return Response({}, status=status.HTTP_201_CREATED)

        preexisting_user.register_preexisting_user(request.data.get('name'))
        LOGGER.info(log_filter(
            request, "registration succeded; "
            "email: '" + str(email) + "'; researcher id: '" +
            str(researcher_id) + "'"
        ))
        return Response({}, status=status.HTTP_201_CREATED)
    except IntegrityError:
        LOGGER.error(log_filter(
            request, "Registration failed: IntegrityError; "
            "email: '" + str(email) + "'; researcher id: '" +
            str(researcher_id) + "'"
        ))
        return Response({}, status=status.HTTP_201_CREATED)
    except user_model.DoesNotExist:
        LOGGER.error(log_filter(
            request, "Registration failed: Email or Researcher Id not found; "
            "email: '" + str(email) + "'; researcher id: '" +
            str(researcher_id) + "'"
        ))
        return Response({}, status=status.HTTP_201_CREATED)
    except KeyError:
        LOGGER.error(log_filter(
            request, "Registration failed: KeyError; " + str(request.data)
        ))
        return Response({}, status=status.HTTP_201_CREATED)


@request_logging_function_view(LOGGER)
@api_view(['POST'])
@authentication_classes((SessionAuthenticationWithUnauthenticatedCSRF, ))
def login(request):
    username = request.data['username']
    password = request.data['password']
    user_model = get_user_model()
    userfound = user_model.objects.filter(email__iexact=username)

    if userfound:
        assert len(userfound) == 1
        user = django.contrib.auth.authenticate(username=userfound[0].email,
                                                password=password)
        if user is not None and user.is_active:
            django.contrib.auth.login(request, user)
            LOGGER.info(log_filter(request, "login success: " + str(username)))
            return Response(status=status.HTTP_204_NO_CONTENT)

    LOGGER.info(log_filter(request, "login failure: " +
                           str(username)))
    return Response(status=status.HTTP_404_NOT_FOUND)


@request_logging_function_view(LOGGER)
@api_view(['POST'])
@authentication_classes((SessionAuthentication, ))
def logout(request):
    django.contrib.auth.logout(request)
    return Response(status=status.HTTP_204_NO_CONTENT)


@request_logging_function_view(LOGGER)
@ensure_csrf_cookie
@api_view(['GET'])
def get_user_info(request):
    user = request.user
    if user.is_authenticated:
        return Response({'loggedIn': True, 'email': user.email,
                         'isAdministrator': user.is_staff},
                        status.HTTP_200_OK)
    else:
        return Response({'loggedIn': False}, status.HTTP_200_OK)


@request_logging_function_view(LOGGER)
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
