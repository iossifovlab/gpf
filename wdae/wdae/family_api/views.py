from rest_framework.response import Response
from rest_framework import status

from query_base.query_base import QueryBaseView


class ListFamiliesView(QueryBaseView):
    def get(self, request, dataset_id):
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if dataset is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        families = dataset.families

        return Response(
            families.keys(),
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
