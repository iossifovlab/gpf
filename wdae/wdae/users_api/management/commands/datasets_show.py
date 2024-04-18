from datasets_api.models import Dataset
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Show all existing datasets"

    def handle(self, *args, **options):
        datasets = Dataset.objects.all()
        for ds in datasets:
            print(
                "{} Authorized groups: {}".format(
                    ds.dataset_id, ",".join([
                        group.name for group in ds.groups.all()
                    ]),
                ),
            )
