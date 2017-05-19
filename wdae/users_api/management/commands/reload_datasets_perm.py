from django.core.management.base import BaseCommand, CommandError
from datasets.config import DatasetsConfig
from datasets_api.models import Dataset


class Command(BaseCommand):
    DEFAULT_GROUPS_FOR_DATASET = ["any_dataset"]

    args = '<file> <file> ...'

    def handle(self, *args, **options):
        if(len(args) != 0):
            raise CommandError('Unexpected argument passed!')

        dataset_config = DatasetsConfig()
        for ds in dataset_config.get_datasets():
            Dataset.add_dataset_perm(ds['id'], ds['authorizedGroups'])
