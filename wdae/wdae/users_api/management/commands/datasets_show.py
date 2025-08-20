from typing import Any

from datasets_api.models import Dataset
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Show all existing datasets"""

    help = "Show all existing datasets"

    def handle(
        self, *args: Any, **options: Any,  # noqa: ARG002
    ) -> None:
        datasets = Dataset.objects.all()
        for ds in datasets:
            group_names: list[str] = [
                group.name for group in ds.groups.all()
            ]
            print(
                f"{ds.dataset_id} Authorized groups: {','.join(group_names)}",
            )
