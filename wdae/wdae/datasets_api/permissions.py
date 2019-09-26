from rest_framework import permissions

from gpf_instance.gpf_instance import get_gpf_instance
from .models import Dataset
from guardian.utils import get_anonymous_user


class IsDatasetAllowed(permissions.BasePermission):

    def has_permission(self, request, view):
        if 'dataset_id' not in request.query_params:
            return True

        return self.has_object_permission(
            request, view, request.query_params['dataset_id'])

    def has_object_permission(self, request, view, dataset_id):
        return self.user_has_permission(request.user, dataset_id)

    @staticmethod
    def user_has_permission(user, dataset_id):
        dataset_object = Dataset.objects.get(dataset_id=dataset_id)
        return user.has_perm('datasets_api.view', dataset_object) or\
            get_anonymous_user().has_perm('datasets_api.view', dataset_object)

    @staticmethod
    def permitted_datasets(user):
        dataset_ids = get_gpf_instance().variants_db.get_all_ids()

        return list(filter(
            lambda dataset_id: IsDatasetAllowed.user_has_permission(
                user, dataset_id),
            dataset_ids))
