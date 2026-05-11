import csv
import os
from typing import Any

from datasets_api.models import Dataset
from datasets_api.permissions import add_group_perm_to_dataset
from django.core.management.base import (
    BaseCommand,
    CommandError,
    CommandParser,
)


class Command(BaseCommand):
    """Add rights to datasets from an input CSV file."""

    help = "Add rights to datasets from an input CSV file"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--file", type=str)

    def handle_dataset(self, dataset: dict[str, str]) -> None:
        dataset_id = dataset["dataset"].strip()
        groups = [gr.strip() for gr in dataset["groups"].split(";")]
        for group_name in groups:
            add_group_perm_to_dataset(group_name, dataset_id)

    def handle(
        self, *args: Any, **options: Any,  # noqa: ARG002
    ) -> None:
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
                f"Successfully restored datasets from file {csvfilename}!"
                "\033[0m",
            )

        except csv.Error as exc:
            raise CommandError(
                f'There was a problem while reading "{csvfilename}"',
            ) from exc
        except OSError as exc:
            raise CommandError(f'File "{csvfilename}" not found') from exc
