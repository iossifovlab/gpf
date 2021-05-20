from rest_framework.response import Response
from rest_framework import status

from dae.variants.attributes import Role

from query_base.query_base import QueryBaseView


class ListAllCollectionsView(QueryBaseView):
    def get(self, request, dataset_id):
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if dataset is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        pscs = dataset.person_set_collections.values()

        result = [psc.to_json() for psc in pscs]

        return Response(
            result,
            status.HTTP_200_OK
        )


class CollectionConfigsView(QueryBaseView):
    def get(self, request, dataset_id):
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if dataset is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(
            dataset.person_set_collection_configs,
            status.HTTP_200_OK
        )


class CollectionStatsView(QueryBaseView):
    def get(self, request, dataset_id, collection_id):
        if dataset_id is None or collection_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = self.gpf_instance.get_genotype_data(dataset_id)

        if (
            dataset is None
            or collection_id not in dataset.person_set_collections
        ):
            return Response(status=status.HTTP_404_NOT_FOUND)

        person_set_collection = dataset.person_set_collections[collection_id]

        result = dict()
        for set_id, person_set in person_set_collection.person_sets.items():
            parents = len(list(
                person_set.get_persons_with_roles(Role.dad, Role.mom)
            ))
            children = len(list(
                person_set.get_persons_with_roles(Role.prb, Role.sib)
            ))
            result[set_id] = {
                "parents": parents,
                "children": children,
            }

        return Response(result, status=status.HTTP_200_OK)
