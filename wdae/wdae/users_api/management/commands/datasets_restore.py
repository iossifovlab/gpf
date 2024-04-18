import csv
import os

from datasets_api.models import Dataset
from datasets_api.permissions import add_group_perm_to_dataset
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Add rights to datasets from an input CSV file"

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str)

    def handle_dataset(self, dataset):
        dataset_id = dataset["dataset"].strip()
        groups = [gr.strip() for gr in dataset["groups"].split(";")]
        for group_name in groups:
            add_group_perm_to_dataset(group_name, dataset_id)

    def handle(self, *args, **options):
        csvfilename = options["file"]
        assert os.path.exists(csvfilename)

        try:
            with open(csvfilename, "rt") as csvfile:
                reader = csv.DictReader(csvfile)
                Dataset.objects.all().delete()
                for dataset in reader:
                    self.handle_dataset(dataset)
            print(
                "\033[92m"
                + f"Successfully restored datasets from file {csvfilename}!"
                + "\033[0m",
            )

        except csv.Error:
            raise CommandError(
                'There was a problem while reading "%s"' % args[0],
            )
        except OSError:
            raise CommandError('File "%s" not found' % args[0])
