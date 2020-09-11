import os
import logging
import glob
import toml

from box import Box

from django.core.management.base import BaseCommand
from datasets_api.models import Dataset
from django.contrib.auth.models import Group
from guardian.shortcuts import get_perms

from gpf_instance.gpf_instance import get_gpf_instance

from pprint import pprint


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Show all existing datasets"

    def add_arguments(self, parser):
        parser.add_argument("old_dataset", type=str)
        parser.add_argument("new_dataset", type=str)

    def get_dataset(self, dataset_id):
        dataset = None
        try:
            dataset = Dataset.objects.get(dataset_id=dataset_id)
        except Exception as ex:
            logger.debug(f"dataset {dataset_id} not found: {ex}")
        return dataset

    def find_dataset_config_file(self, dataset_id):
        config = get_gpf_instance().get_genotype_data_config(dataset_id)
        assert config is not None

        conf_dir = config.conf_dir

        result = glob.glob(os.path.join(conf_dir, "*.conf"))
        assert len(result) == 1, \
            f"unexpected number of config files in {conf_dir}"
        config_file = result[0]
        assert os.path.exists(config_file)
        return config_file

    def find_dataset_config(self, dataset_id):
        config_file = self.find_dataset_config_file(dataset_id)

        with open(config_file, "r") as infile:
            short_config = toml.load(infile)
            short_config = Box(short_config)
        return short_config

    def get_genotype_storage(self, config):
        gpf_instance = get_gpf_instance()
        genotype_storage = gpf_instance \
            .genotype_storage_db \
            .get_genotype_storage(
                config.genotype_storage.id)
        return genotype_storage

    def is_impala_genotype_storage(self, config):
        assert config.genotype_storage
        genotype_storage = self.get_genotype_storage(config)
        return genotype_storage.is_impala

    def dataset_rename_hdfs_directory(self, config, new_id):
        genotype_storage = self.get_genotype_storage(config)
        hdfs_helpers = genotype_storage.hdfs_helpers

        source_dir = genotype_storage.default_hdfs_study_path(config.id)
        dest_dir = genotype_storage.default_hdfs_study_path(new_id)

        print(source_dir)
        print(dest_dir)

        assert hdfs_helpers.exists(source_dir), \
            f"source hdfs dir {source_dir} should exists"

        assert hdfs_helpers.isdir(source_dir), \
            f"source hdfs dir {source_dir} should be a directory"

        assert not hdfs_helpers.exists(dest_dir), \
            f"destination hdfs dir {dest_dir} should not exists"

        hdfs_helpers.rename(source_dir, dest_dir)

    def dataset_rename_impala_tables(self, config, new_id):
        genotype_storage = self.get_genotype_storage(config)

        impala_db = genotype_storage.storage_config.impala.db
        impala_helpers = genotype_storage.impala_helpers

        hdfs_study = genotype_storage.default_hdfs_study_path(new_id)
        hdfs_pedigree = os.path.join(hdfs_study, "pedigree")
        hdfs_variants = os.path.join(hdfs_study, "variants")

        pedigree_table = genotype_storage._construct_pedigree_table(new_id)
        variants_table = genotype_storage._construct_variants_table(new_id)

        impala_helpers.change_table_location(
            impala_db, config.genotype_storage.tables.pedigree, hdfs_pedigree)
        impala_helpers.change_table_location(
            impala_db, config.genotype_storage.tables.variants, hdfs_variants)

        assert not impala_helpers.check_table(impala_db, pedigree_table), \
            f"table {pedigree_table} should not exists"
        assert not impala_helpers.check_table(impala_db, variants_table), \
            f"table {variants_table} should not exists"

        impala_helpers.rename_table(
            impala_db,
            config.genotype_storage.tables.pedigree,
            pedigree_table)
        impala_helpers.rename_table(
            impala_db,
            config.genotype_storage.tables.variants,
            variants_table)

        return pedigree_table, variants_table

    def rename_study_config(self, dataset_id, new_id, short_config):
        pprint(short_config)

        config_file = self.find_dataset_config_file(dataset_id)
        os.rename(config_file, f"{config_file}_bak")
        config_dirname = os.path.dirname(config_file)
        new_dirname = os.path.join(os.path.dirname(config_dirname), new_id)
        print(new_dirname)
        os.rename(config_dirname, new_dirname)

        new_config_file = os.path.join(new_dirname, f"{new_id}.conf")

        with open(new_config_file, "wt") as outfile:
            content = toml.dumps(short_config)
            outfile.write(content)

    def handle(self, *args, **options):
        assert "old_dataset" in options and options["old_dataset"] is not None
        assert "new_dataset" in options and options["new_dataset"] is not None

        dataset_id = options["old_dataset"]
        dataset_id = dataset_id.strip()
        dataset = self.get_dataset(dataset_id)

        logger.debug(f"dataset found: {dataset.dataset_id}")

        new_id = options["new_dataset"]
        assert self.get_dataset(new_id) is None, \
            f"dataset {new_id} already exists"

        config = get_gpf_instance().get_genotype_data_config(dataset_id)
        assert config is not None

        assert self.is_impala_genotype_storage(config), \
            f"genotype storage {config.genotype_storage.id} is not Impala"

        self.dataset_rename_hdfs_directory(config, new_id)
        pedigree_table, variants_table = \
            self.dataset_rename_impala_tables(config, new_id)

        short_config = self.find_dataset_config(dataset_id)
        print(pedigree_table, variants_table)
        pprint(short_config)

        short_config.id = new_id
        short_config.genotype_storage.tables.pedigree = pedigree_table
        if variants_table:
            short_config.genotype_storage.tables.variants = variants_table

        self.rename_study_config(dataset_id, new_id, short_config)
