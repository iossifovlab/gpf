from rest_framework.response import Response
from rest_framework import status
from query_base.query_base import QueryBaseView

from dae.pedigrees.family_tag_builder import FamilyTagsBuilder, check_tag


class ListFamiliesView(QueryBaseView):
    def get(self, request, dataset_id):
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if dataset is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        families = dataset.families

        tags = request.GET.get("tags")
        if tags is None:
            return Response(
                families.keys(),
                status.HTTP_200_OK
            )

        result = []
        tags = tags.split(",")
        for family_id, family in families.items():
            for tag in tags:
                try:
                    tagged = check_tag(family, tag, True)
                    if tagged:
                        result.append(family_id)
                except ValueError as e:
                    print(e)
                    return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(
            result,
            status.HTTP_200_OK
        )


class FamilyDetailsView(QueryBaseView):
    def get(self, request, dataset_id, family_id):
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
            status=status.HTTP_200_OK
        )


class TagsView(QueryBaseView):
    def get(self, request):
        # pylint: disable=unused-argument,no-self-use
        return Response(
            list(FamilyTagsBuilder.TAGS.keys()),
            status=status.HTTP_200_OK
        )


class ListMembersView(QueryBaseView):
    def get(self, request, dataset_id, family_id):
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
            status=status.HTTP_200_OK
        )


class MemberDetailsView(QueryBaseView):
    def get(self, request, dataset_id, family_id, member_id):
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
            status=status.HTTP_200_OK
        )


class AllMemberDetailsView(QueryBaseView):
    def get(self, request, dataset_id, family_id):
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
            status=status.HTTP_200_OK
        )


class ListAllDetailsView(QueryBaseView):
    def get(self, request, dataset_id):
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)

        if dataset is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        families = dataset.families

        out = []

        for family_id, family in families.items():
            json = family.to_json()
            members = family.members_in_order
            json["members"] = [m.to_json() for m in members]
            out.append(json)

        return Response(
            out,
            status=status.HTTP_200_OK
        )
