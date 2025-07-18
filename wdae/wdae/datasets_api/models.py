import logging
from collections.abc import Iterable
from typing import Any

from django.contrib.auth.models import Group
from django.db import models

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
    def default_groups(self) -> list[str]:
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
    def set_broken(cls, dataset_id: str, *, broken: bool) -> None:
        """
        Set a Dataset object's broken status to the given value.

        Datasets should be flagged broken before loading and checked
        after loading to be unflagged.
        """
        try:
            # pylint: disable=no-member
            dataset_object = cls.objects.get(dataset_id=dataset_id)
        except Dataset.DoesNotExist:
            logger.exception("Failed validating %s", dataset_id)
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
            logger.exception("Failed updating %s", dataset_id)
            return
        dataset_object.dataset_name = dataset_name
        dataset_object.save()


class DatasetHierarchy(models.Model):
    """Data for dataset hierarchy and inheritance."""

    instance_id: models.TextField = models.TextField()
    ancestor: models.ForeignKey[Any, Dataset] = models.ForeignKey(
        Dataset, on_delete=models.CASCADE, related_name="ancestor",
    )
    descendant: models.ForeignKey[Any, Dataset] = models.ForeignKey(
        Dataset, on_delete=models.CASCADE, related_name="descendant",
    )
    direct: models.BooleanField = models.BooleanField()

    @classmethod
    def clear(cls, instance_id: str) -> None:
        """Clear the model's records."""
        cls.objects.filter(instance_id=instance_id).delete()

    @classmethod
    def add_relation(
        cls, instance_id: str, ancestor_id: str,
        descendant_id: str, *,
        direct: bool = False,
    ) -> None:
        """Add a relation to the hierarchy with provided dataset IDs."""
        ancestor = Dataset.objects.get(dataset_id=ancestor_id)
        descendant = Dataset.objects.get(dataset_id=descendant_id)
        cls.objects.create(
            instance_id=instance_id,
            ancestor=ancestor,
            descendant=descendant,
            direct=direct,
        )

    @classmethod
    def is_study(cls, instance_id: str, dataset: Dataset) -> bool:
        """
        Return whether a dataset is a study.

        A dataset without children is a study and not a group.
        """
        return len(cls.objects.filter(
            instance_id=instance_id,
            ancestor_id=dataset.pk,
        ).exclude(descendant_id=dataset.pk)) == 0

    @classmethod
    def get_parents(
        cls, instance_id: str, dataset: Dataset, *,
        direct: bool | None = None,
    ) -> list[Dataset]:
        """Return all parents of a given dataset."""
        if direct is True:
            relations = cls.objects.filter(
                instance_id=instance_id,
                descendant_id=dataset.pk,
                direct=True,
            ).exclude(ancestor_id=dataset.pk)
        else:
            relations = cls.objects.filter(
                instance_id=instance_id,
                descendant_id=dataset.pk,
            ).exclude(ancestor_id=dataset.pk)
        return [relation.ancestor for relation in relations]

    @classmethod
    def get_direct_datasets_parents(
        cls, instance_id: str, datasets: Iterable[Dataset],
    ) -> dict[str, list[str]]:
        """Return dictionary of parents for a list of DB datasets."""
        dataset_ids = [ds.pk for ds in datasets]
        relations = cls.objects.filter(
            instance_id=instance_id, descendant_id__in=dataset_ids,
        )

        result: dict[str, list[str]] = {ds.dataset_id: [] for ds in datasets}
        for relation in relations:
            if relation.direct:
                result[relation.descendant.dataset_id].append(
                    relation.ancestor.dataset_id)

        return result

    @classmethod
    def get_children(
        cls, instance_id: str, dataset: Dataset, *,
        direct: bool | None = None,
    ) -> list[Dataset]:
        """Return all children of a given dataset."""
        if direct is True:
            relations = cls.objects.filter(
                instance_id=instance_id,
                ancestor_id=dataset.pk,
                direct=True,
            ).exclude(descendant_id=dataset.pk)
        else:
            relations = cls.objects.filter(
                instance_id=instance_id,
                ancestor_id=dataset.pk,
            ).exclude(descendant_id=dataset.pk)
        return [relation.descendant for relation in relations]
