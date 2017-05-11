from django.core.management.base import BaseCommand, CommandError
from datasets.config import DatasetsConfig
from datasets_api.models import Dataset
from django.contrib.auth.models import Group
from guardian.shortcuts import assign_perm, remove_perm


class Command(BaseCommand):
    DEFAULT_GROUPS_FOR_DATASET = ["any_dataset"]

    args = '<file> <file> ...'

    def handle(self, *args, **options):
        if(len(args) != 0):
            raise CommandError('Unexpected argument passed!')

        dataset_config = DatasetsConfig()
        for ds in dataset_config.get_datasets():
            dataset_id = ds['id']
            datasetObject, _ =\
                Dataset.objects.get_or_create(dataset_id=dataset_id)

            for group in Group.objects.all():
                remove_perm('view', group, datasetObject)

            groups = [dataset_id]
            if ds['authorizedGroups'] is not None:
                groups += ds['authorizedGroups']
            if self.DEFAULT_GROUPS_FOR_DATASET is not None:
                groups += self.DEFAULT_GROUPS_FOR_DATASET
            for group_name in groups:
                group, created = Group.objects.get_or_create(name=group_name)
                assign_perm('view', group, datasetObject)
