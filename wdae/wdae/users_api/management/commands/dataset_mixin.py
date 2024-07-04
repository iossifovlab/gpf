import logging

from datasets_api.models import Dataset
from django.contrib.auth.models import Group
from django.db.models import Q

from dae.studies.dataset_helpers import DatasetHelpers

logger = logging.getLogger(__name__)


class DatasetBaseMixin(DatasetHelpers):
    """Mixin for dataset management."""

    def get_dataset(self, dataset_id: str) -> Dataset | None:
        """Get dataset by id."""
        try:
            genotype_data = self.gpf_instance.get_genotype_data(dataset_id)
            if genotype_data is None:
                logger.info("genotype data %s not found", dataset_id)
                return None

            return Dataset.objects.get(dataset_id=dataset_id)
        except Exception:
            logger.debug("dataset %s not found", dataset_id, exc_info=True)
        return None

    def rename_wdae_dataset_and_groups(
            self, dataset_id: str, new_id: str, dry_run: bool = False) -> None:
        """Rename WDAE dataset and groups."""
        dataset = self.get_dataset(dataset_id)
        assert dataset is not None, f"can't find WDAE dataset {dataset_id}"

        logger.info(
            "going to rename wdae dataset group name from %s to %s",
            dataset_id, new_id)
        if not dry_run:
            dataset.dataset_id = new_id
            dataset.save()

        new_groups = Group.objects.filter(Q(name=new_id))
        if len(new_groups) > 0:
            assert len(new_groups) == 1
            new_groups.delete()

        groups = list(Group.objects.filter(
            Q(groupobjectpermission__permission__codename="view"),
            Q(name=dataset_id)))
        if len(groups) == 0:
            logger.warning(
                "wdae group %s not found; nothing to rename", dataset_id)
        else:
            if len(groups) != 1:
                logger.warning("more than one group found: %s", groups)

            for group in groups:
                logger.info(
                    "going to rename wdae dataset group from %s to %s",
                    dataset_id, new_id)
                if not dry_run:
                    group.name = new_id
                    group.save()

    def remove_wdae_dataset_and_groups(
            self, dataset_id: str, dry_run: bool = False) -> None:
        """Remove WDAE dataset and groups."""
        dataset = self.get_dataset(dataset_id)
        assert dataset is not None, f"can't find WDAE dataset {dataset_id}"
        logger.info("going ro remove wdae dataset %s", dataset_id)
        if not dry_run:
            dataset.delete()

        groups = Group.objects.filter(
            Q(groupobjectpermission__permission__codename="view"),
            Q(name=dataset_id))
        if len(groups) == 0:
            logger.warning(
                "wdae group %s not found; nothing to remove", dataset_id)
        else:
            assert len(groups) == 1

            logger.info("going ro remove wdae dataset group %s", dataset_id)
            if not dry_run:
                groups.delete()
