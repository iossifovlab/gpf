import sys
from django.core.management.base import BaseCommand
from datasets_api.models import Dataset
from django.contrib.auth.models import Group
from guardian.shortcuts import get_perms


class Command(BaseCommand):
    help = "Export all existing datasets"

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str)

    def handle(self, *args, **options):
        groups = Group.objects.all()

        if options["file"]:
            outfile = open(options["file"], "w")
        else:
            outfile = sys.stdout

        datasets = Dataset.objects.all()
        print("dataset,groups", file=outfile)
        for ds in datasets:
            authorized = [
                group.name
                for group in groups
                if "view" in get_perms(group, ds)
            ]
            authorized = ";".join(authorized)
            print(f"{ds.dataset_id},{authorized}", file=outfile)
