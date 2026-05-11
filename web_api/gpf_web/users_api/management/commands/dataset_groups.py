import logging
from typing import Any

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandParser
from django.db.models import Q

from .dataset_mixin import DatasetBaseMixin

logger = logging.getLogger(__name__)


class Command(BaseCommand, DatasetBaseMixin):
    """Check an existing dataset access groups."""

    help = "Check an existing dataset access groups"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("dataset", type=str)

    def handle(self, *_args: Any, **options: Any) -> None:
        assert "dataset" in options
        assert options["dataset"] is not None

        dataset_id = options["dataset"]
        dataset_id = dataset_id.strip()
        dataset = self.get_dataset(dataset_id)

        if dataset is None:
            logger.error("Dataset not found: %s", dataset_id)
            return

        logger.debug("dataset found: %s", dataset.dataset_id)

        groups = list(Group.objects.filter(
            Q(groupobjectpermission__permission__codename="view"),
            Q(name=dataset_id)))

        for group in groups:
            logger.debug(
                "group %s (%s), %s, %s",
                group.name, group.pk, group.pk, dir(group))
