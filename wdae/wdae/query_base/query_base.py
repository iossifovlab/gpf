"""Provides base class for query views."""

from rest_framework import views  # type: ignore
from oauth2_provider.contrib.rest_framework import OAuth2Authentication

from gpf_instance.gpf_instance import get_gpf_instance
from datasets_api.permissions import IsDatasetAllowed


class QueryBaseView(views.APIView):
    """Base class for query views."""

    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsDatasetAllowed,)

    def __init__(self):
        super().__init__()
        self.gpf_instance = get_gpf_instance()
        self.variants_db = self.gpf_instance._variants_db
        self.pheno_db = self.gpf_instance._pheno_db

    @staticmethod
    def get_permitted_datasets(user):
        return IsDatasetAllowed.permitted_datasets(user)
