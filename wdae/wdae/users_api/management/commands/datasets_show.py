from django.core.management.base import BaseCommand
from datasets_api.models import Dataset
from django.contrib.auth.models import Group
from guardian.shortcuts import get_perms


class Command(BaseCommand):
    args = "<email>"
    help = "Shows all information about user"

    def handle(self, *args, **options):
        groups = Group.objects.all()

        datasets = Dataset.objects.all()
        for ds in datasets:
            authorized = [
                group.name
                for group in groups
                if "view" in get_perms(group, ds)
            ]
            print(
                "{} Authorized groups: {}".format(
                    ds.dataset_id, ",".join(authorized)
                )
            )
