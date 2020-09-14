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

from pprint import pprint


logger = logging.getLogger(__name__)


class DatasetBaseMixin:

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

        source_dir = genotype_storage.full_hdfs_path(
            genotype_storage.default_hdfs_study_path(config.id))
        dest_dir = genotype_storage.full_hdfs_path(
            genotype_storage.default_hdfs_study_path(new_id))

        assert hdfs_helpers.exists(source_dir), \
            f"source hdfs dir {source_dir} should exists"

        assert hdfs_helpers.isdir(source_dir), \
            f"source hdfs dir {source_dir} should be a directory"

        assert not hdfs_helpers.exists(dest_dir), \
            f"destination hdfs dir {dest_dir} should not exists"

        hdfs_helpers.rename(source_dir, dest_dir)

    def check_dataset_hdfs_directories(self, config):
        genotype_storage = self.get_genotype_storage(config)
        hdfs_helpers = genotype_storage.hdfs_helpers

        study_dir = genotype_storage.full_hdfs_path(
            genotype_storage.default_hdfs_study_path(config.id))

        assert hdfs_helpers.exists(study_dir), \
            f"study hdfs dir {study_dir} should exists"
        assert hdfs_helpers.isdir(study_dir), \
            f"study hdfs dir {study_dir} should be a directory"

        variants_dir = os.path.join(study_dir, "variants")
        assert hdfs_helpers.exists(variants_dir), \
            f"variants hdfs dir {variants_dir} should exists"
        assert hdfs_helpers.isdir(variants_dir), \
            f"variants hdfs dir {variants_dir} should be a directory"

        pedigree_dir = os.path.join(study_dir, "pedigree")
        assert hdfs_helpers.exists(pedigree_dir), \
            f"pedigree hdfs dir {pedigree_dir} should exists"
        assert hdfs_helpers.isdir(pedigree_dir), \
            f"pedigree hdfs dir {pedigree_dir} should be a directory"

        pedigree_file = os.path.join(pedigree_dir, "pedigree.parquet")
        assert hdfs_helpers.exists(pedigree_file), \
            f"pedigree hdfs file {pedigree_file} should exists"
        assert hdfs_helpers.isfile(pedigree_file), \
            f"pedigree hdfs file {pedigree_file} should be a file"

    def dataset_recreate_impala_tables(self, config, new_id):
        genotype_storage = self.get_genotype_storage(config)

        impala_db = genotype_storage.storage_config.impala.db
        impala_helpers = genotype_storage.impala_helpers

        new_hdfs_variants = genotype_storage \
            .default_variants_hdfs_dirname(new_id)

        new_variants_table = genotype_storage._construct_variants_table(new_id)

        impala_helpers.recreate_table(
            impala_db, config.genotype_storage.tables.variants,
            new_variants_table, new_hdfs_variants)

        new_hdfs_pedigree = genotype_storage \
            .default_pedigree_hdfs_filename(new_id)
        new_hdfs_pedigree = os.path.dirname(new_hdfs_pedigree)

        new_pedigree_table = genotype_storage._construct_pedigree_table(new_id)

        impala_helpers.recreate_table(
            impala_db, config.genotype_storage.tables.pedigree,
            new_pedigree_table, new_hdfs_pedigree)

        return new_pedigree_table, new_variants_table

    def check_dataset_impala_tables(self, config):
        genotype_storage = self.get_genotype_storage(config)

        impala_db = genotype_storage.storage_config.impala.db
        impala_helpers = genotype_storage.impala_helpers

        variants_table = config.genotype_storage.tables.variants
        assert impala_helpers.check_table(impala_db, variants_table), \
            f"impala variants table {impala_db}.{variants_table} should exists"

        pedigree_table = config.genotype_storage.tables.pedigree
        assert impala_helpers.check_table(impala_db, pedigree_table), \
            f"impala pedigree table {impala_db}.{pedigree_table} should exists"

    def rename_study_config(self, dataset_id, new_id, short_config):

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

    def rename_wdae_dataset_and_groups(self, dataset_id, new_id):
        dataset = self.get_dataset(dataset_id)
        assert dataset is not None, f"can't find WDAE dataset {dataset_id}"

        dataset.dataset_id = new_id
        dataset.save()

        new_groups = Group.objects.filter(Q(name=new_id))
        if len(new_groups) > 0:
            assert len(new_groups) == 1
            new_groups.delete()

        groups = list(Group.objects.filter(
            Q(groupobjectpermission__permission__codename="view"),
            Q(name__iregex=dataset_id)))
        assert len(groups) == 1
        group = groups[0]

        group.name = new_id
        group.save()
