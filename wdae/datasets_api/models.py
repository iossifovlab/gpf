from django.db import models
from django.contrib.auth.models import Group
from guardian.shortcuts import assign_perm, remove_perm
from helpers.logger import LOGGER


class Dataset(models.Model):
    dataset_id = models.TextField()

    DEFAULT_GROUPS_FOR_DATASET = ["any_dataset"]

    class Meta:
        permissions = (
            ('view', 'View dataset'),
        )

    def __repr__(self):
        return self.dataset_id

    @classmethod
    def recreate_dataset_perm(cls, dataset_id, authorized_groups=None):
        datasetObject, _ = cls.objects.get_or_create(dataset_id=dataset_id)

        groups = [dataset_id]
        if authorized_groups is not None:
            groups += authorized_groups
        if cls.DEFAULT_GROUPS_FOR_DATASET is not None:
            groups += cls.DEFAULT_GROUPS_FOR_DATASET
        LOGGER.error("recreating groups: {}".format(groups))
        for group_name in set(groups):
            group, _created = Group.objects.get_or_create(name=group_name)
            assign_perm('view', group, datasetObject)
