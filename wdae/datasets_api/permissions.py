'''
Created on Jul 5, 2017

@author: lubo
'''
from rest_framework import permissions
from datasets_api.models import Dataset
from guardian.utils import get_anonymous_user


class IsDatasetAllowed(permissions.BasePermission):

    def has_object_permission(self, request, view, dataset_id):
        user = request.user
        dataset_object = Dataset.objects.get(dataset_id=dataset_id)
        return user.has_perm('datasets_api.view', dataset_object) or\
            get_anonymous_user().has_perm('datasets_api.view', dataset_object)
