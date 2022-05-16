from django.core.management.base import BaseCommand
from datasets_api.models import Dataset


class Command(BaseCommand):
    help = "Show all existing datasets"

    def handle(self, *args, **options):
        datasets = Dataset.objects.all()
        for ds in datasets:
            authorized = [group.name for group in ds.groups.all()]
            print(
                "{} Authorized groups: {}".format(
                    ds.dataset_id, ",".join(authorized)
                )
            )
