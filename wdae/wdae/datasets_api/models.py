import logging
from typing import List

from django.db import models
from django.contrib.auth.models import Group


logger = logging.getLogger(__name__)


class Dataset(models.Model):
    """Datasets and permissions on datasets."""

    dataset_id: models.TextField = models.TextField()
    dataset_name: models.TextField = models.TextField(default="")
    broken: models.BooleanField = models.BooleanField(default=True)
    groups: models.ManyToManyField = models.ManyToManyField(Group)

    def __repr__(self) -> str:
        return str(self.dataset_id)

    @property
    def default_groups(self) -> List[str]:
        return ["any_dataset", self.dataset_id]

    @classmethod
    def recreate_dataset_perm(cls, dataset_id: str) -> None:
        """Add the default groups to a dataset object."""
        logger.debug("looking for dataset <%s>", dataset_id)
        # pylint: disable=no-member
        dataset_object, _ = cls.objects.get_or_create(
            dataset_id=dataset_id)
        for group_name in dataset_object.default_groups:
            group, _created = Group.objects.get_or_create(name=group_name)
            dataset_object.groups.add(group)

    @classmethod
    def set_broken(cls, dataset_id: str, broken: bool) -> None:
        """
        Set a Dataset object's broken status to the given value.

        Datasets should be flagged broken before loading and checked
        after loading to be unflagged.
        """
        try:
            # pylint: disable=no-member
            dataset_object = cls.objects.get(dataset_id=dataset_id)
        except Dataset.DoesNotExist:
            logger.error("Failed validating %s", dataset_id)
            return
        dataset_object.broken = broken
        dataset_object.save()

    @classmethod
    def update_name(cls, dataset_id: str, dataset_name: str) -> None:
        """Update a Dataset object's name to the given value."""
        try:
            # pylint: disable=no-member
            dataset_object = cls.objects.get(dataset_id=dataset_id)
        except Dataset.DoesNotExist:
            logger.error("Failed updating %s", dataset_id)
            return
        dataset_object.dataset_name = dataset_name
        dataset_object.save()
