import logging
from typing import Any, ClassVar

from datasets_api.models import Dataset
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models import Count, Q
from django.db.models.query import QuerySet
from gpf_instance.gpf_instance import permission_update
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import api_view
from rest_framework.decorators import (
    authentication_classes as authentication_classes_decorator,
)
from rest_framework.request import Request
from rest_framework.response import Response
from utils.authentication import (
    GPFOAuth2Authentication,
    ReadOnlyDBAuthentication,
    SessionAuthenticationWithoutCSRF,
)

from .serializers import (
    GroupCreateSerializer,
    GroupRetrieveSerializer,
    GroupSerializer,
)

logger = logging.getLogger(__name__)


class GroupsViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.ReadOnlyModelViewSet,
):
    # pylint: disable=too-many-ancestors
    """Groups view set."""

    authentication_classes: ClassVar[list[type]] = [
        SessionAuthenticationWithoutCSRF, GPFOAuth2Authentication]

    serializer_class = GroupSerializer
    permission_classes = (permissions.IsAdminUser,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ("name",)
    lookup_field = "name"

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        auth = ReadOnlyDBAuthentication()
        auth.authenticate(request)
        return super().create(request, *args, **kwargs)

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        auth = ReadOnlyDBAuthentication()
        auth.authenticate(request)
        return super().update(request, *args, **kwargs)

    def partial_update(
        self, request: Request, *args: Any, **kwargs: Any,
    ) -> Response:
        auth = ReadOnlyDBAuthentication()
        auth.authenticate(request)
        return super().partial_update(request, *args, **kwargs, partial=True)

    def get_serializer_class(  # pyright: ignore
        self,
    ) -> type[GroupSerializer]:
        serializer_class = self.serializer_class

        if self.action in {"list", "retrieve"}:
            serializer_class = GroupRetrieveSerializer
        elif self.action == "create":
            serializer_class = GroupCreateSerializer

        return serializer_class  # pyright: ignore

    def get_queryset(self) -> QuerySet:  # pyright: ignore
        # Get groups that have users or datasets tagged with it
        return Group.objects.annotate(
            users_count=Count("user"), datasets_count=Count("dataset"),
        ).filter(
            Q(users_count__gt=0) | Q(datasets_count__gt=0),
        ).order_by("name")


@api_view(["POST"])
@authentication_classes_decorator((
    ReadOnlyDBAuthentication,
    GPFOAuth2Authentication,
    SessionAuthenticationWithoutCSRF,
))
@permission_update
def add_group_to_dataset(request: Request) -> Response:
    """Add group to dataset."""
    if not request.user.is_authenticated:
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    if not request.user.is_staff:
        return Response(status=status.HTTP_403_FORBIDDEN)
    if not (
            "datasetId" in request.data and  # pyright: ignore
            "groupName" in request.data):  # pyright: ignore
        return Response(status=status.HTTP_400_BAD_REQUEST)

    dataset = Dataset.objects.get(
        dataset_id=request.data["datasetId"])  # pyright: ignore
    group, _ = Group.objects.get_or_create(
        name=request.data["groupName"])  # pyright: ignore
    dataset.groups.add(group)
    return Response(status=status.HTTP_200_OK)


@api_view(["POST"])
@authentication_classes_decorator((
    ReadOnlyDBAuthentication,
    GPFOAuth2Authentication,
    SessionAuthenticationWithoutCSRF,
))
@permission_update
def remove_group_from_dataset(request: Request) -> Response:
    """Remove group from dataset."""
    if not request.user.is_authenticated:
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    if not request.user.is_staff:
        return Response(status=status.HTTP_403_FORBIDDEN)
    if not (
            "datasetId" in request.data  # pyright: ignore
            and "groupId" in request.data):  # pyright: ignore
        return Response(status=status.HTTP_400_BAD_REQUEST)

    dataset = Dataset.objects.get(
        dataset_id=request.data["datasetId"])  # pyright: ignore
    group = Group.objects.get(
        pk=request.data["groupId"])  # pyright: ignore
    if group.name in dataset.default_groups:
        return Response(status=status.HTTP_403_FORBIDDEN)
    dataset.groups.remove(group)
    return Response(status=status.HTTP_200_OK)


@api_view(["POST"])
@authentication_classes_decorator((
    ReadOnlyDBAuthentication,
    GPFOAuth2Authentication,
    SessionAuthenticationWithoutCSRF,
))
@permission_update
def add_user_to_group(request: Request) -> Response:
    """Add user to group."""
    if not request.user.is_authenticated:
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    if not request.user.is_staff:
        return Response(status=status.HTTP_403_FORBIDDEN)
    if not (
            "userEmail" in request.data  # pyright: ignore
            and "groupName" in request.data):  # pyright: ignore
        return Response(status=status.HTTP_400_BAD_REQUEST)
    data = request.data
    email = data["userEmail"]  # pyright: ignore
    group_name = data["groupName"]  # pyright: ignore
    user_model = get_user_model()

    if not user_model.objects.filter(email=email).exists():
        logger.info("User with email %s does not exist...", email)
        return Response(status=status.HTTP_404_NOT_FOUND)
    user = user_model.objects.get(email=email)

    group, _ = Group.objects.get_or_create(name=group_name)

    user.groups.add(group)  # pyright: ignore
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
@authentication_classes_decorator((
    ReadOnlyDBAuthentication,
    GPFOAuth2Authentication,
    SessionAuthenticationWithoutCSRF,
))
@permission_update
def remove_user_from_group(request: Request) -> Response:
    """Remove user from group."""
    if not request.user.is_authenticated:
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    if not request.user.is_staff:
        return Response(status=status.HTTP_403_FORBIDDEN)
    if not (
            "userEmail" in request.data  # pyright: ignore
            and "groupName" in request.data):  # pyright: ignore
        return Response(status=status.HTTP_400_BAD_REQUEST)
    data = request.data
    email = data["userEmail"]  # pyright: ignore
    group_name = data["groupName"]  # pyright: ignore
    user_model = get_user_model()

    if not user_model.objects.filter(email=email).exists():
        logger.info("User with email %s does not exist...", email)
        return Response(status=status.HTTP_404_NOT_FOUND)
    user = user_model.objects.get(email=email)

    if not Group.objects.filter(name=group_name).exists():
        logger.info("Group %s does not exist...", group_name)
        return Response(status=status.HTTP_404_NOT_FOUND)
    group = Group.objects.get(name=group_name)

    user.groups.remove(group)  # pyright: ignore
    return Response(status=status.HTTP_204_NO_CONTENT)
