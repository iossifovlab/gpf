import logging

from django.db.models import Q
from django.contrib.auth.models import Group
from datasets_api.models import Dataset

from dae.backends.impala.import_commons import DatasetHelpers


logger = logging.getLogger(__name__)


class DatasetBaseMixin(DatasetHelpers):

    def get_dataset(self, dataset_id):
        dataset = None
        try:
            dataset = Dataset.objects.get(dataset_id=dataset_id)
        except Exception as ex:
            logger.debug(f"dataset {dataset_id} not found: {ex}")
        return dataset

    def rename_wdae_dataset_and_groups(self, dataset_id, new_id):
        dataset = self.get_dataset(dataset_id)
        assert dataset is not None, f"can't find WDAE dataset {dataset_id}"

        dataset.dataset_id = new_id
        dataset.save()

        new_groups = Group.objects.filter(Q(name=new_id))
        if len(new_groups) > 0:
            assert len(new_groups) == 1
            new_groups.delete()

        groups = list(Group.objects.filter(
            Q(groupobjectpermission__permission__codename="view"),
            Q(name=dataset_id)))
        assert len(groups) == 1
        group = groups[0]

        group.name = new_id
        group.save()

    def remove_wdae_dataset_and_groups(self, dataset_id):
        dataset = self.get_dataset(dataset_id)
        assert dataset is not None, f"can't find WDAE dataset {dataset_id}"
        dataset.delete()

        groups = Group.objects.filter(
            Q(groupobjectpermission__permission__codename="view"),
            Q(name=dataset_id))
        assert len(groups) == 1
        groups.delete()
