from query_base.query_base import QueryBaseView
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response


class CollectionConfigsView(QueryBaseView):
    """Serve person set collections configuration view."""

    def get(self, _request: Request, dataset_id: str) -> Response:
        """Get person set collections configurations."""
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if dataset is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        result = {
            psc.id: psc.config_json()
            for psc in dataset.person_set_collections.values()
        }
        return Response(
            result,
            status.HTTP_200_OK,
        )


class CollectionDomainView(QueryBaseView):
    """Serve person set collections domain view."""

    def get(self, _request: Request, dataset_id: str) -> Response:
        """Get person set collections domains."""
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if dataset is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        result = {
            psc.id: psc.domain_json()
            for psc in dataset.person_set_collections.values()
        }
        return Response(
            result,
            status.HTTP_200_OK,
        )


class CollectionStatsView(QueryBaseView):
    """Serve person set collections statistics view."""

    def get(
        self, _request: Request, dataset_id: str, collection_id: str,
    ) -> Response:
        """Get person set collection statistics."""
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
            person_set_collection.get_stats(), status=status.HTTP_200_OK,
        )
