import sys
import logging

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from guardian.shortcuts import get_perms

from .dataset_mixin import DatasetBaseMixin

logger = logging.getLogger(__name__)


class Command(BaseCommand, DatasetBaseMixin):
    help = "Export all existing datasets"

    def __init__(self, **kwargs):
        DatasetBaseMixin.__init__(self)
        BaseCommand.__init__(self, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str)

    def handle(self, *args, **options):
        groups = Group.objects.all()

        if options["file"]:
            outfile = open(options["file"], "w")
        else:
            outfile = sys.stdout

        print("dataset,groups", file=outfile)
        for genotype_data_id in self.gpf_instance.get_genotype_data_ids():
            try:
                dataset = self.get_dataset(genotype_data_id)
                authorized = [
                    group.name
                    for group in groups
                    if "view" in get_perms(group, dataset)
                ]
                authorized = ";".join(authorized)
                print(f"{dataset.dataset_id},{authorized}", file=outfile)
            except Exception as ex:
                logger.warning(f"dataset {genotype_data_id} not found")
                logger.exception(ex)
