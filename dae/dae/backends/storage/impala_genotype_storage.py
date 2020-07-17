import os
import sys
import glob
from time import time

from dae.backends.raw.loader import VariantsLoader, TransmissionType
from dae.backends.storage.genotype_storage import GenotypeStorage

from dae.backends.impala.hdfs_helpers import HdfsHelpers
from dae.backends.impala.impala_helpers import ImpalaHelpers
from dae.backends.impala.impala_variants import ImpalaFamilyVariants
from dae.backends.impala.parquet_io import NoPartitionDescriptor, \
    ParquetManager, \
    ParquetPartitionDescriptor

from dae.configuration.study_config_builder import StudyConfigBuilder
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.utils.dict_utils import recursive_dict_update


class ImpalaGenotypeStorage(GenotypeStorage):

    def __init__(self, storage_config):
        super(ImpalaGenotypeStorage, self).__init__(storage_config)
        self.data_dir = self.storage_config.dir

        impala_hosts = self.storage_config.impala.hosts
        impala_port = self.storage_config.impala.port
        pool_size = self.storage_config.impala.pool_size

        self._impala_helpers = ImpalaHelpers(
            impala_hosts=impala_hosts, impala_port=impala_port,
            pool_size=pool_size
        )
        self._hdfs_helpers = None

    def get_db(self):
        return self.storage_config.impala.db

    def is_impala(self):
        return True

    @property
    def impala_helpers(self):
        assert self._impala_helpers is not None
        return self._impala_helpers

    @property
    def hdfs_helpers(self):
        if self._hdfs_helpers is None:
            self._hdfs_helpers = HdfsHelpers(
                self.storage_config.hdfs.host,
                self.storage_config.hdfs.port
            )

        assert self._hdfs_helpers is not None
        return self._hdfs_helpers

    @classmethod
    def study_tables(cls, study_config):
        storage_config = study_config.genotype_storage
        if storage_config and storage_config.tables \
                and storage_config.tables.pedigree \
                and storage_config.tables.variants:

            variants_table = storage_config.tables.variants
            pedigree_table = storage_config.tables.pedigree

        elif storage_config and storage_config.tables \
                and storage_config.tables.pedigree:

            variants_table = None
            pedigree_table = storage_config.tables.pedigree

        else:
            # default study tables
            variants_table = cls._construct_variants_table(
                study_config.id)
            pedigree_table = cls._construct_pedigree_table(
                study_config.id)
        return variants_table, pedigree_table

    @staticmethod
    def _construct_variants_table(study_id):
        return f"{study_id}_variants"

    @staticmethod
    def _construct_pedigree_table(study_id):
        return f"{study_id}_pedigree"

    def build_backend(self, study_config, genomes_db):
        assert study_config is not None

        variants_table, pedigree_table = self.study_tables(study_config)
        family_variants = ImpalaFamilyVariants(
            self.impala_helpers,
            self.storage_config.impala.db,
            variants_table,
            pedigree_table,
            genomes_db.get_gene_models(),
        )

        return family_variants

    def _generate_study_config(
        self, study_id, pedigree_table, variants_table=None
    ):
        assert study_id is not None

        study_config = {
            "id": study_id,
            "conf_dir": ".",
            "has_denovo": False,
            "genotype_storage": {
                "id": self.storage_config.section_id(),
                "tables": {"pedigree": pedigree_table},
            },
            "genotype_browser": {"enabled": False},
        }

        if variants_table:
            storage_config = study_config["genotype_storage"]
            storage_config["tables"]["variants"] = variants_table
            study_config["genotype_browser"]["enabled"] = True

        return study_config

    def simple_study_import(
            self,
            study_id,
            families_loader=None,
            variant_loaders=None,
            study_config=None,
            output=".",
            include_reference=False):

        parquet_pedigrees = []
        parquet_variants = []
        parquet_filenames = None
        has_denovo = False
        has_cnv = False
        bucket_index = 0

        if variant_loaders:
            for index, variant_loader in enumerate(variant_loaders):
                assert isinstance(variant_loader, VariantsLoader), \
                    type(variant_loader)

                if variant_loader.get_attribute("source_type") == "denovo":
                    has_denovo = True

                if variant_loader.get_attribute("source_type") == "cnv":
                    has_denovo = True
                    has_cnv = True

                if variant_loader.transmission_type == \
                        TransmissionType.denovo:
                    assert index < 100

                    bucket_index = index  # denovo buckets < 100
                elif variant_loader.transmission_type == \
                        TransmissionType.transmitted:
                    bucket_index = index + 100  # transmitted buckets >=100

                parquet_filenames = ParquetManager.build_parquet_filenames(
                    output, bucket_index=bucket_index, study_id=study_id)

                ParquetManager.variants_to_parquet_filename(
                    variant_loader,
                    parquet_filenames.variants,
                    bucket_index=bucket_index,
                    include_reference=include_reference
                )
                parquet_variants.append(parquet_filenames.variants_dirname)
        else:
            parquet_filenames = ParquetManager.build_parquet_filenames(
                output, bucket_index=0, study_id=study_id
            )

        families = families_loader.load()
        ParquetManager.families_to_parquet(
            families, parquet_filenames.pedigree
        )

        parquet_pedigrees.append(parquet_filenames.pedigree)

        if parquet_variants:
            assert all([pv == parquet_variants[0] for pv in parquet_variants])
            variants_path = parquet_variants[0]
        else:
            variants_path = None

        config_dict = self.impala_load_dataset(
            study_id,
            variants_path=variants_path,
            pedigree_file=parquet_pedigrees[0]
        )

        config_dict["has_denovo"] = has_denovo
        config_dict["has_cnv"] = has_cnv

        if study_config is not None:
            study_config_dict = GPFConfigParser.load_config_raw(study_config)
            config_dict = recursive_dict_update(config_dict, study_config_dict)

        config_builder = StudyConfigBuilder(config_dict)

        return config_builder.build_config()

    def hdfs_upload_dataset(
            self, study_id, variants_dir,
            pedigree_file, partition_description):

        study_path = os.path.join(self.storage_config.hdfs.base_dir, study_id)
        pedigree_hdfs_path = os.path.join(
            study_path, "pedigree", "pedigree.parquet"
        )
        self.hdfs_helpers.put(pedigree_file, pedigree_hdfs_path)

        if variants_dir is None:
            return (None, pedigree_hdfs_path)

        files_glob = partition_description.generate_file_access_glob()
        files_glob = os.path.join(variants_dir, files_glob)
        variants_files = glob.glob(files_glob)

        variants_hdfs_path = os.path.join(study_path, "variants")
        variants_hdfs_filenames = []
        basedir = partition_description.variants_filename_basedir(
            variants_files[0])
        assert basedir, (variants_files[0], basedir)

        for parquet_file in variants_files:
            file_dir = os.path.dirname(parquet_file)
            file_dir = file_dir[len(basedir):]
            file_hdfs_dir = os.path.join(variants_hdfs_path, file_dir)
            self.hdfs_helpers.makedirs(file_hdfs_dir)
            self.hdfs_helpers.put_in_directory(parquet_file, file_hdfs_dir)
            variants_hdfs_filenames.append(
                os.path.join(file_hdfs_dir, os.path.basename(parquet_file)))

        return (variants_hdfs_filenames[0], pedigree_hdfs_path)

    def impala_import_dataset(
            self, study_id,
            pedigree_hdfs_file,
            variants_hdfs_file,
            partition_description):

        pedigree_table = self._construct_pedigree_table(study_id)
        variants_table = self._construct_variants_table(study_id)

        db = self.storage_config.impala.db

        self.impala_helpers.drop_table(db, variants_table)
        self.impala_helpers.drop_table(db, pedigree_table)

        self.impala_helpers.import_dataset_into_db(
            db,
            pedigree_table,
            variants_table,
            pedigree_hdfs_file,
            variants_hdfs_file,
            partition_description)

        return self._generate_study_config(
            study_id, pedigree_table, variants_table)

    def impala_load_dataset(self, study_id, variants_path, pedigree_file):
        partition_config_file = os.path.join(
            variants_path, "_PARTITION_DESCRIPTION"
        )
        if os.path.exists(partition_config_file):
            partition_description = ParquetPartitionDescriptor.from_config(
                partition_config_file, root_dirname=variants_path)
        else:
            partition_description = NoPartitionDescriptor(
                root_dirname=variants_path)

        variants_hdfs_path, pedigree_hdfs_path = \
            self.hdfs_upload_dataset(
                study_id, variants_path, pedigree_file, partition_description)

        return self.impala_import_dataset(
            study_id,
            pedigree_hdfs_path,
            variants_hdfs_path,
            partition_description=partition_description)


STUDY_CONFIG_TEMPLATE = """
id = "{id}"
conf_dir = "."

[genotype_storage]
id = "{genotype_storage}"

[genotype_storage.tables]
pedigree = "{pedigree_table}"
variants = "{variants_table}"
"""
