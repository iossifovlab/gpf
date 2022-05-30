from rest_framework import views

from gpf_instance.gpf_instance import get_gpf_instance

from datasets_api.permissions import IsDatasetAllowed
from users_api.authentication import SessionAuthenticationWithoutCSRF


class QueryBaseView(views.APIView):

    authentication_classes = (SessionAuthenticationWithoutCSRF,)
    permission_classes = (IsDatasetAllowed,)

    def __init__(self):
        self.gpf_instance = get_gpf_instance()
        self.variants_db = self.gpf_instance._variants_db
        self.pheno_db = self.gpf_instance._pheno_db

    def get_permitted_datasets(self, user):
        return IsDatasetAllowed.permitted_datasets(user)
