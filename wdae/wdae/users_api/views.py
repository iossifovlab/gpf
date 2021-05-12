import json
from functools import wraps

from django.db import IntegrityError, transaction
from django.contrib.auth import get_user_model
from django.contrib.auth.models import BaseUserManager, Group
from django.shortcuts import get_object_or_404, get_list_or_404
from django.views.decorators.csrf import ensure_csrf_cookie
from django.conf import settings
from django.http.response import StreamingHttpResponse
from django.db.models import Q
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

from .authentication import SessionAuthenticationWithUnauthenticatedCSRF
from .models import VerificationPath
from .serializers import UserSerializer
from .serializers import UserWithoutEmailSerializer
from .serializers import BulkGroupOperationSerializer

from utils.logger import log_filter, LOGGER, request_logging
from utils.logger import request_logging_function_view
from utils.email_regex import is_email_valid

from django.utils.decorators import available_attrs

from utils.streaming_response_util import convert


def csrf_clear(view_func):
    """
    Skips the CSRF checks by setting the 'csrf_processing_done' to true.
    """

    def wrapped_view(*args, **kwargs):
        request = args[0]
        request.csrf_processing_done = True
        return view_func(*args, **kwargs)

    return wraps(view_func, assigned=available_attrs(view_func))(wrapped_view)


def iterator_to_json(users):
    yield "["
    curr = next(users, None)
    post = next(users, None)
    while curr is not None:
        if curr.email:
            serializer = UserSerializer
        else:
            serializer = UserWithoutEmailSerializer
        yieldval = json.dumps(serializer(curr).data, default=convert)
        if post is None:
            yield yieldval
            break
        else:
            yield yieldval + ","
        curr = post
        post = next(users, None)
    yield "]"
    return 0


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset = get_user_model().objects.all()
    permission_classes = (permissions.IsAdminUser,)
    pagination_class = None
    filter_backends = (filters.SearchFilter,)
    search_fields = ("groups__name", "email", "name")

    @request_logging(LOGGER)
    def list(self, request):
        return super(UserViewSet, self).list(request)

    @request_logging(LOGGER)
    def create(self, request):
        return super(UserViewSet, self).create(request)

    @request_logging(LOGGER)
    def retrieve(self, request, pk=None):
        return super(UserViewSet, self).retrieve(request, pk=pk)

    @request_logging(LOGGER)
    def update(self, request, pk=None, *args, **kwargs):
        return super(UserViewSet, self).update(request, pk=pk, *args, **kwargs)

    @request_logging(LOGGER)
    def partial_update(self, request, pk=None):
        return super(UserViewSet, self).partial_update(request, pk=pk)

    @request_logging(LOGGER)
    def destroy(self, request, pk=None):
        return super(UserViewSet, self).destroy(request, pk=pk)

    def get_serializer_class(self):
        serializer_class = self.serializer_class

        if self.action == "update" or self.action == "partial_update":
            serializer_class = UserWithoutEmailSerializer

        return serializer_class

    @request_logging(LOGGER)
    @action(detail=False, methods=["get"])
    def streaming_search(self, request):
        self.check_permissions(request)
        queryset = get_user_model().objects.all()
        search_param = request.GET.get("search", None)
        if search_param:
            queryset = queryset.filter(
                Q(name__icontains=search_param)
                | Q(email__icontains=search_param)
            )
        return StreamingHttpResponse(
            iterator_to_json(queryset.iterator()),
            status=status.HTTP_200_OK,
            content_type="text/event-stream",
        )

    @request_logging(LOGGER)
    @action(detail=True, methods=["post"])
    def password_reset(self, request, pk=None):
        self.check_permissions(request)
        user = get_object_or_404(get_user_model(), pk=pk)

        user.reset_password(by_admin=True)
        user.deauthenticate()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @request_logging(LOGGER)
    @action(detail=False, methods=["post"])
    def bulk_add_groups(self, request):
        self.check_permissions(request)

        serializer = BulkGroupOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        users = get_list_or_404(get_user_model(), id__in=data["userIds"])
        if len(users) != len(data["userIds"]):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            for group_name in data["groups"]:
                group, _ = Group.objects.get_or_create(name=group_name)
                group.user_set.add(*users)

        return Response(status=status.HTTP_200_OK)

    @request_logging(LOGGER)
    @action(detail=False, methods=["post"])
    def bulk_remove_groups(self, request):
        serializer = BulkGroupOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        users = get_list_or_404(get_user_model(), id__in=data["userIds"])
        if len(users) != len(data["userIds"]):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            for group_name in data["groups"]:
                group = get_object_or_404(Group, name=group_name)
                group.user_set.remove(*users)

        return Response(status=status.HTTP_200_OK)


@request_logging_function_view(LOGGER)
@api_view(["POST"])
def reset_password(request):
    email = request.data["email"]
    user_model = get_user_model()
    try:
        user = user_model.objects.get(email=email)
        user.reset_password()
        user.deauthenticate()

        return Response({}, status.HTTP_200_OK)
    except user_model.DoesNotExist:
        return Response({}, status=status.HTTP_200_OK)


@request_logging_function_view(LOGGER)
@api_view(["POST"])
def change_password(request):
    password = request.data["password"]
    verif_path = request.data["verifPath"]

    get_user_model().change_password(verif_path, password)

    return Response({}, status.HTTP_201_CREATED)


@request_logging_function_view(LOGGER)
@api_view(["POST"])
def register(request):
    user_model = get_user_model()

    try:
        email = BaseUserManager.normalize_email(request.data["email"])
        if not is_email_valid(email):
            raise ValueError

        if settings.OPEN_REGISTRATION:
            preexisting_user, _ = user_model.objects.get_or_create(email=email)
        else:
            preexisting_user = user_model.objects.get(
                email__iexact=email
            )

        preexisting_user.register_preexisting_user(request.data.get("name"))
        LOGGER.info(
            log_filter(
                request,
                "registration succeded; "
                "email: '"
                + str(email)
                + "'",
            )
        )
        return Response({}, status=status.HTTP_201_CREATED)
    except IntegrityError:
        LOGGER.error(
            log_filter(
                request,
                "Registration failed: IntegrityError; "
                "email: '"
                + str(email)
                + "'",
            )
        )
        return Response({}, status=status.HTTP_201_CREATED)
    except user_model.DoesNotExist:
        LOGGER.error(
            log_filter(
                request,
                "Registration failed: Email or Researcher Id not found; "
                "email: '"
                + str(email)
                + "'",
            )
        )
        return Response(
            {"error_msg": ("Registration is closed."
                           " Please contact an administrator.")},
            status=status.HTTP_403_FORBIDDEN
        )
    except KeyError:
        LOGGER.error(
            log_filter(
                request, "Registration failed: KeyError; " + str(request.data)
            )
        )
        return Response({}, status=status.HTTP_201_CREATED)
    except ValueError:
        LOGGER.error(
            log_filter(
                request,
                f"Registration failed: Invalid email; email: '{str(email)}'"
            )
        )
        return Response(
            {"error_msg": ("Invalid email address entered."
                           " Please use a valid email address.")},
            status=status.HTTP_400_BAD_REQUEST
        )


@request_logging_function_view(LOGGER)
@csrf_clear
@api_view(["POST"])
@authentication_classes((SessionAuthenticationWithUnauthenticatedCSRF,))
def login(request):
    username = request.data["username"]
    password = request.data["password"]
    user_model = get_user_model()
    userfound = user_model.objects.filter(email__iexact=username)

    if userfound:
        assert len(userfound) == 1
        user = django.contrib.auth.authenticate(
            username=userfound[0].email, password=password
        )
        if user is not None and user.is_active:
            django.contrib.auth.login(request, user)
            LOGGER.info(log_filter(request, "login success: " + str(username)))
            return Response(status=status.HTTP_204_NO_CONTENT)

    LOGGER.info(log_filter(request, "login failure: " + str(username)))
    return Response(status=status.HTTP_404_NOT_FOUND)


@request_logging_function_view(LOGGER)
@csrf_clear
@api_view(["POST"])
@authentication_classes((SessionAuthentication,))
def logout(request):
    django.contrib.auth.logout(request)
    return Response(status=status.HTTP_204_NO_CONTENT)


@request_logging_function_view(LOGGER)
@ensure_csrf_cookie
@api_view(["GET"])
def get_user_info(request):
    user = request.user
    if user.is_authenticated:
        return Response(
            {
                "loggedIn": True,
                "email": user.email,
                "isAdministrator": user.is_staff,
            },
            status.HTTP_200_OK,
        )
    else:
        return Response({"loggedIn": False}, status.HTTP_200_OK)


@request_logging_function_view(LOGGER)
@api_view(["POST"])
def check_verif_path(request):
    verif_path = request.data["verifPath"]
    try:
        VerificationPath.objects.get(path=verif_path)
        return Response({}, status=status.HTTP_200_OK)
    except VerificationPath.DoesNotExist:
        return Response(
            {"errors": "Verification path does not exist."},
            status=status.HTTP_400_BAD_REQUEST,
        )
