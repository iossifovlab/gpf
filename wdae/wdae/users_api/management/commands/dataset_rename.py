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

from gpf_instance.gpf_instance import get_gpf_instance
from .dataset_mixin import DatasetBaseMixin

from pprint import pprint


logger = logging.getLogger(__name__)


class Command(BaseCommand, DatasetBaseMixin):
    help = "Rename an existing dataset"

    def add_arguments(self, parser):
        parser.add_argument("old_dataset", type=str)
        parser.add_argument("new_dataset", type=str)

    def handle(self, *args, **options):
        assert "old_dataset" in options and options["old_dataset"] is not None
        assert "new_dataset" in options and options["new_dataset"] is not None

        dataset_id = options["old_dataset"]
        dataset_id = dataset_id.strip()
        dataset = self.get_dataset(dataset_id)
        assert dataset is not None, \
            f"dataset {dataset_id} should exists"

        logger.debug(f"dataset found: {dataset.dataset_id}")

        new_id = options["new_dataset"]
        assert self.get_dataset(new_id) is None, \
            f"dataset {new_id} already exists"

        config = get_gpf_instance().get_genotype_data_config(dataset_id)
        assert config is not None

        genotype_data = get_gpf_instance().get_genotype_data(dataset_id)
        print(type(genotype_data), genotype_data)

        if genotype_data.is_group:
            short_config = self.find_dataset_config(dataset_id)
            short_config.id = new_id

            self.rename_study_config(dataset_id, new_id, short_config)
            self.rename_wdae_dataset_and_groups(dataset_id, new_id)

        else:
            assert self.is_impala_genotype_storage(config), \
                f"genotype storage {config.genotype_storage.id} is not Impala"

            self.dataset_rename_hdfs_directory(config, new_id)
            pedigree_table, variants_table = \
                self.dataset_recreate_impala_tables(config, new_id)

            short_config = self.find_dataset_config(dataset_id)

            short_config.id = new_id
            short_config.genotype_storage.tables.pedigree = pedigree_table
            if variants_table:
                short_config.genotype_storage.tables.variants = variants_table

            self.rename_study_config(dataset_id, new_id, short_config)
            self.rename_wdae_dataset_and_groups(dataset_id, new_id)
