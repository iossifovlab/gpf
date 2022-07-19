"""Module containing the base view for data-related views."""
from rest_framework import views  # type: ignore

from gpf_instance.gpf_instance import get_gpf_instance
from datasets_api.permissions import IsDatasetAllowed

from utils.authentication import GPFOAuth2Authentication


class QueryBaseView(views.APIView):
    """
    Base classfor data-related views.

    Provides custom OAuth2 authentication and an automatic dataset
    permissions check.
    """

    authentication_classes = (GPFOAuth2Authentication,)
    permission_classes = (IsDatasetAllowed,)

    def __init__(self):
        super().__init__()
        self.gpf_instance = get_gpf_instance()
        self.variants_db = self.gpf_instance._variants_db
        self.pheno_db = self.gpf_instance._pheno_db

    @staticmethod
    def get_permitted_datasets(user):
        return IsDatasetAllowed.permitted_datasets(user)
