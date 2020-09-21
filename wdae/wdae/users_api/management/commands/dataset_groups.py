import os
import re
import logging
import glob
import toml

from box import Box

from django.db.models import Count, Q
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from guardian.shortcuts import get_perms
from datasets_api.models import Dataset

from .dataset_mixin import DatasetBaseMixin

from gpf_instance.gpf_instance import get_gpf_instance

from pprint import pprint


logger = logging.getLogger(__name__)


class Command(BaseCommand, DatasetBaseMixin):
    help = "Check an existing dataset access groups"

    def add_arguments(self, parser):
        parser.add_argument("dataset", type=str)

    def handle(self, *args, **options):
        assert "dataset" in options and options["dataset"] is not None

        dataset_id = options["dataset"]
        dataset_id = dataset_id.strip()
        dataset = self.get_dataset(dataset_id)

        logger.debug(f"dataset found: {dataset.dataset_id}")

        groups = list(Group.objects.filter(
            Q(groupobjectpermission__permission__codename="view"),
            Q(name=dataset_id)))

        for group in groups:
            logger.debug(
                f"group {group.name} ({group.id}), {group.pk}, {dir(group)}")
