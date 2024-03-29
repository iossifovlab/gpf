"""Module containing the base view for data-related views."""
from rest_framework import views  # type: ignore

from django.contrib.auth.models import User

from gpf_instance.gpf_instance import get_wgpf_instance, recreated_dataset_perm
from datasets_api.permissions import IsDatasetAllowed

from utils.authentication import GPFOAuth2Authentication


class QueryBaseView(views.APIView):
    """
    Base class for data-related views.

    Provides custom OAuth2 authentication and an automatic dataset
    permissions check.
    """

    authentication_classes = (GPFOAuth2Authentication,)

    def __init__(self) -> None:
        super().__init__()
        self.gpf_instance = get_wgpf_instance()
        self.instance_id = self.gpf_instance.instance_id
        recreated_dataset_perm(self.gpf_instance)
        self.variants_db = self.gpf_instance._variants_db
        self.pheno_registry = self.gpf_instance._pheno_registry

    @staticmethod
    def get_permitted_datasets(user: User) -> list[str]:
        return IsDatasetAllowed.permitted_datasets(user)


class QueryDatasetView(QueryBaseView):
    permission_classes = [IsDatasetAllowed]
