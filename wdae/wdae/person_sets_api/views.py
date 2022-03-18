from rest_framework.response import Response  # type: ignore
from rest_framework import status  # type: ignore

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
        return Response(
            person_set_collection.get_stats(), status=status.HTTP_200_OK
        )
