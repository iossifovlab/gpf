from rest_framework import permissions

from gpf_instance.gpf_instance import get_gpf_instance
from .models import Dataset
from utils.datasets import find_dataset_id_in_request
from guardian.utils import get_anonymous_user
from guardian.shortcuts import get_groups_with_perms


class IsDatasetAllowed(permissions.BasePermission):
    def has_permission(self, request, view):
        dataset_id = find_dataset_id_in_request(request)

        if dataset_id is None:
            return True

        return self.has_object_permission(request, view, dataset_id)

    def has_object_permission(self, request, view, dataset_id):
        if not self.user_has_permission(request.user, dataset_id):
            if not Dataset.objects.filter(dataset_id=dataset_id).exists():
                return False
            dataset_object = Dataset.objects.get(dataset_id=dataset_id)
            for group in get_groups_with_perms(dataset_object):
                if Dataset.objects.filter(dataset_id=group.name).exists():
                    if self.user_has_permission(request.user, group.name):
                        return True
            return False
        return True

    @staticmethod
    def user_has_permission(user, dataset_id):
        try:
            dataset_object = Dataset.objects.get(dataset_id=dataset_id)
        except Dataset.DoesNotExist:
            print("dataset ", dataset_id, "does not exists...")
            return False
        return user.has_perm(
            "datasets_api.view", dataset_object
        ) or get_anonymous_user().has_perm("datasets_api.view", dataset_object)

    @staticmethod
    def permitted_datasets(user):
        dataset_ids = get_gpf_instance().get_genotype_data_ids()

        return list(
            filter(
                lambda dataset_id: IsDatasetAllowed.user_has_permission(
                    user, dataset_id
                ),
                dataset_ids,
            )
        )
