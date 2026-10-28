from typing import cast

from datasets_api.partial_grants import get_granted_person_set_collection
from datasets_api.permissions import get_permissions_etag
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views.decorators.http import etag
from query_base.query_base import DatasetAccessRightsView, QueryBaseView
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response


class CollectionConfigsView(QueryBaseView, DatasetAccessRightsView):
    """Serve person set collections configuration view."""

    @method_decorator(etag(get_permissions_etag))
    def get(self, _request: Request, dataset_id: str) -> Response:
        """Get person set collections configurations."""
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if dataset is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if dataset.is_phenotype:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        result = {
            psc.id: psc.config_json()
            for psc in dataset.genotype_data.person_set_collections.values()
        }
        return Response(
            result,
            status.HTTP_200_OK,
        )


class CollectionDomainView(QueryBaseView, DatasetAccessRightsView):
    """Serve person set collections domain view."""

    @method_decorator(etag(get_permissions_etag))
    def get(self, _request: Request, dataset_id: str) -> Response:
        """Get person set collections domains."""
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if dataset is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if dataset.is_phenotype:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        result = {
            psc.id: psc.domain_json()
            for psc in dataset.genotype_data.person_set_collections.values()
        }
        return Response(
            result,
            status.HTTP_200_OK,
        )


class CollectionStatsView(QueryBaseView, DatasetAccessRightsView):
    """Serve person set collections statistics view."""

    def get(
        self, request: Request, dataset_id: str, collection_id: str,
    ) -> Response:
        """Get person set collection statistics."""
        if dataset_id is None or collection_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = self.gpf_instance.get_genotype_data(dataset_id)
        if dataset is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        person_set_collection = get_granted_person_set_collection(
            self.gpf_instance, cast(User, request.user), dataset,
            collection_id,
        )
        if person_set_collection is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(
            person_set_collection.get_stats(), status=status.HTTP_200_OK,
        )
