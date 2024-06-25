from datasets_api.permissions import (
    get_instance_timestamp_etag,
    get_permissions_etag,
)
from django.utils.decorators import method_decorator
from django.views.decorators.http import etag
from query_base.query_base import QueryDatasetView
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response

from dae.pedigrees.family_tag_builder import FamilyTag, check_tag


class ListFamiliesView(QueryDatasetView):
    """List dataåset families."""

    @method_decorator(etag(get_permissions_etag))
    def get(self, request: Request, dataset_id: str) -> Response:
        """Response to get request for a dataset families."""
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if dataset is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        families = dataset.families

        tags_query = request.GET.get("tags")
        if tags_query is None:
            return Response(
                families.keys(),
                status.HTTP_200_OK,
            )

        result = set()
        tag_labels = tags_query.split(",")
        tags = {FamilyTag.from_label(label) for label in tag_labels}
        for family_id, family in families.items():
            for tag in tags:
                try:
                    tagged = check_tag(family, tag)
                    if tagged:
                        result.add(family_id)
                except ValueError as err:
                    print(err)
                    return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(
            result,
            status.HTTP_200_OK,
        )


class FamilyDetailsView(QueryDatasetView):
    """Get a family details view."""

    @method_decorator(etag(get_permissions_etag))
    def get(
        self, request: Request, dataset_id: str, family_id: str,
    ) -> Response:
        # pylint: disable=unused-argument
        """Response to a get request for the details of a specific family."""
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if family_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)

        if dataset is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        families = dataset.families

        family = families.get(family_id)

        if family is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(
            family.to_json(),
            status=status.HTTP_200_OK,
        )


class TagsView(QueryDatasetView):

    @method_decorator(etag(get_instance_timestamp_etag))
    def get(self, request: Request) -> Response:
        # pylint: disable=unused-argument
        return Response(
            list(FamilyTag.all_labels()),
            status=status.HTTP_200_OK,
        )


class ListMembersView(QueryDatasetView):
    """List family members view."""

    @method_decorator(etag(get_permissions_etag))
    def get(
        self, request: Request, dataset_id: str, family_id: str,
    ) -> Response:
        # pylint: disable=unused-argument
        """Response to get family members."""
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if family_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)

        if dataset is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        families = dataset.families

        family = families.get(family_id)

        if family is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(
            family.members_ids,
            status=status.HTTP_200_OK,
        )


class MemberDetailsView(QueryDatasetView):
    """Details view of a person."""

    @method_decorator(etag(get_permissions_etag))
    def get(
        self, request: Request, dataset_id: str,
        family_id: str, member_id: str,
    ) -> Response:
        # pylint: disable=unused-argument
        """Response to get request for a person details."""
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if family_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if member_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)

        if dataset is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        families = dataset.families

        family = families.get(family_id)

        if family is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        member = family.get_member(member_id)

        if member is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(
            member.to_json(),
            status=status.HTTP_200_OK,
        )


class AllMemberDetailsView(QueryDatasetView):
    """Details of all members of a family."""

    @method_decorator(etag(get_permissions_etag))
    def get(
        self, request: Request, dataset_id: str, family_id: str,
    ) -> Response:
        # pylint: disable=unused-argument
        """Response to get request for details of all members of a family."""
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if family_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)

        if dataset is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        families = dataset.families

        family = families.get(family_id)

        if family is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        members = family.members_in_order

        if members is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(
            [m.to_json() for m in members],
            status=status.HTTP_200_OK,
        )


class ListAllDetailsView(QueryDatasetView):
    """List of all family details."""

    @method_decorator(etag(get_permissions_etag))
    def get(self, request: Request, dataset_id: str) -> Response:
        # pylint: disable=unused-argument
        """Response to get request for all families details in a dataset."""
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)

        if dataset is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        families = dataset.families

        out = []

        for _, family in families.items():
            json = family.to_json()
            members = family.members_in_order
            json["members"] = [m.to_json() for m in members]
            out.append(json)

        return Response(
            out,
            status=status.HTTP_200_OK,
        )
