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
    help = "Check an existing dataset"

    def add_arguments(self, parser):
        parser.add_argument("dataset", type=str)

    def handle(self, *args, **options):
        assert "dataset" in options and options["dataset"] is not None

        dataset_id = options["dataset"]
        dataset_id = dataset_id.strip()
        dataset = self.get_dataset(dataset_id)

        logger.debug(f"dataset found: {dataset.dataset_id}")

        assert dataset is not None

        config = get_gpf_instance().get_genotype_data_config(dataset_id)
        assert config is not None

        assert self.is_impala_genotype_storage(config), \
            f"genotype storage {config.genotype_storage.id} is not Impala"

        self.check_dataset_hdfs_directories(config)
        self.check_dataset_impala_tables(config)
