import logging

from django.db.models import Q
from django.contrib.auth.models import Group
from datasets_api.models import Dataset

from dae.studies.dataset_helpers import DatasetHelpers


logger = logging.getLogger(__name__)


class DatasetBaseMixin(DatasetHelpers):

    def get_dataset(self, dataset_id):
        try:
            genotype_data = self.gpf_instance.get_genotype_data(dataset_id)
            if genotype_data is None:
                logger.info(f"genotype data {dataset_id} not found")
                return None

            return Dataset.objects.get(dataset_id=dataset_id)
        except Exception as ex:
            logger.debug(f"dataset {dataset_id} not found: {ex}")
        return None

    def rename_wdae_dataset_and_groups(
            self, dataset_id, new_id, dry_run=None):

        dataset = self.get_dataset(dataset_id)
        assert dataset is not None, f"can't find WDAE dataset {dataset_id}"

        logger.info(
            f"going to rename wdae dataset group name from {dataset_id} "
            f"to {new_id}")
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
                f"wdae group {dataset_id} not found; nothing to rename")
        else:
            if len(groups) != 1:
                logger.warning(f"more than one group found: {groups}")

            for group in groups:
                logger.info(
                    f"going to rename wdae dataset group from {dataset_id} "
                    f"to {new_id}")
                if not dry_run:
                    group.name = new_id
                    group.save()

    def remove_wdae_dataset_and_groups(self, dataset_id, dry_run=None):
        dataset = self.get_dataset(dataset_id)
        assert dataset is not None, f"can't find WDAE dataset {dataset_id}"
        logger.info(f"going ro remove wdae dataset {dataset_id}")
        if not dry_run:
            dataset.delete()

        groups = Group.objects.filter(
            Q(groupobjectpermission__permission__codename="view"),
            Q(name=dataset_id))
        if len(groups) == 0:
            logger.warning(
                f"wdae group {dataset_id} not found; nothing to remove")
        else:
            assert len(groups) == 1

            logger.info(f"going ro remove wdae dataset group {dataset_id}")
            if not dry_run:
                groups.delete()
