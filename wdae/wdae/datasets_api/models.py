import logging

from django.db import models
from django.contrib.auth.models import Group
from utils.logger import LOGGER


logger = logging.getLogger(__name__)


class Dataset(models.Model):
    dataset_id: models.TextField = models.TextField()
    groups = models.ManyToManyField(Group)

    DEFAULT_GROUPS_FOR_DATASET = ["any_dataset"]

    class Meta(object):
        permissions = (("view", "View dataset"),)

    @property
    def default_groups(self):
        return self.DEFAULT_GROUPS_FOR_DATASET + [self.dataset_id]

    def __repr__(self):
        return self.dataset_id

    @classmethod
    def recreate_dataset_perm(cls, dataset_id, authorized_groups=None):
        logger.debug(f"looking for dataset <{dataset_id}>")
        dataset_object, _ = cls.objects.get_or_create(dataset_id=dataset_id)

        groups = dataset_object.default_groups
        if authorized_groups is not None:
            groups += authorized_groups
        LOGGER.debug("recreating groups: {}".format(groups))
        for group_name in set(groups):
            group, _created = Group.objects.get_or_create(name=group_name)
            dataset_object.groups.add(group)
