import csv
import os
from datasets_api.permissions import add_group_perm_to_dataset
from django.core.management.base import BaseCommand, CommandError
from datasets_api.models import Dataset
# from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = "Export all existing datasets"

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str)

    def handle_dataset(self, dataset):
        print(dataset)
        dataset_id = dataset["dataset"].strip()
        groups = [gr.strip() for gr in dataset["groups"].split(";")]
        print(dataset_id)
        print(groups)
        for group_name in groups:
            # dataset_has_group_perm(dataset_id, group_name)
            add_group_perm_to_dataset(group_name, dataset_id)

    def handle(self, *args, **options):
        # groups = Group.objects.all()

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
                + "\033[0m"
            )

        except csv.Error:
            raise CommandError(
                'There was a problem while reading "%s"' % args[0]
            )
        except IOError:
            raise CommandError('File "%s" not found' % args[0])

        # datasets = Dataset.objects.all()
        # print("dataset,groups", file=outfile)
        # for ds in datasets:
        #     authorized = [
        #         group.name
        #         for group in groups
        #         if "view" in get_perms(group, ds)
        #     ]
        #     authorized = ";".join(authorized)
        #     print(f"{ds.dataset_id},{authorized}", file=outfile)
