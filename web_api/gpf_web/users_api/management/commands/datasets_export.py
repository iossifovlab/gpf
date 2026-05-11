import logging
import sys
from typing import Any, TextIO

from django.core.management.base import BaseCommand

from .dataset_mixin import DatasetBaseMixin

logger = logging.getLogger(__name__)


class Command(BaseCommand, DatasetBaseMixin):
    """Export all existing datasets to a CSV file."""

    help = "Export all existing datasets"

    def __init__(self, **kwargs: Any) -> None:
        gpf_instance = kwargs.pop("gpf_instance", None)
        DatasetBaseMixin.__init__(self, gpf_instance=gpf_instance)
        BaseCommand.__init__(self, **kwargs)

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--file", type=str)

    def handle(self, *args: Any, **options: Any) -> None:  # noqa: ARG002
        # pylint: disable=consider-using-with
        if options["file"]:
            outfile: TextIO = open(options["file"], "w")  # noqa: SIM115
        else:
            outfile = sys.stdout

        print("dataset,groups", file=outfile)
        for genotype_data_id in self.gpf_instance.get_genotype_data_ids():
            try:
                dataset = self.get_dataset(genotype_data_id)
                assert dataset is not None, "dataset not found"

                authorized = ";".join([
                    group.name for group in dataset.groups.all()
                ])
                print(f"{genotype_data_id},{authorized}", file=outfile)
            except Exception:
                logger.exception("dataset %s not found", genotype_data_id)
