import os
import glob
import logging

import toml

from dae.backends.raw.loader import VariantsLoader, TransmissionType
from dae.backends.storage.genotype_storage import GenotypeStorage

from dae.backends.impala.hdfs_helpers import HdfsHelpers
from dae.backends.impala.impala_helpers import ImpalaHelpers
from dae.backends.impala.impala_variants import ImpalaVariants
from dae.backends.impala.parquet_io import NoPartitionDescriptor, \
    ParquetManager, \
    ParquetPartitionDescriptor

from dae.configuration.study_config_builder import StudyConfigBuilder
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.utils.dict_utils import recursive_dict_update
from dae.backends.impala.rsync_helpers import RsyncHelpers


logger = logging.getLogger(__name__)


class ImpalaGenotypeStorage(GenotypeStorage):
    """Defines Apache Impala genotype storage."""

    def __init__(self, storage_config, section_id):
        super().__init__(storage_config, section_id)

        impala_hosts = self.storage_config.impala.hosts
        impala_port = self.storage_config.impala.port
        pool_size = self.storage_config.impala.pool_size

        self._impala_helpers = ImpalaHelpers(
            impala_hosts=impala_hosts, impala_port=impala_port,
            pool_size=pool_size)

        self._hdfs_helpers = None
        self._rsync_helpers = None
        if self.storage_config.rsync:
            self._rsync_helpers = RsyncHelpers(
                self.storage_config.rsync.location)

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
        """Create and return an HDFS helpers object."""
        if self._hdfs_helpers is None:
            self._hdfs_helpers = HdfsHelpers(
                self.storage_config.hdfs.host,
                self.storage_config.hdfs.port,
                replication=self.storage_config.hdfs.replication
            )

        assert self._hdfs_helpers is not None
        return self._hdfs_helpers

    @property
    def rsync_helpers(self):
        return self._rsync_helpers

    @classmethod
    def study_tables(cls, study_config):
        """Return variants and pedigree tables names for a study."""
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

    def build_backend(self, study_config, genome, gene_models):
        assert study_config is not None

        variants_table, pedigree_table = self.study_tables(study_config)
        family_variants = ImpalaVariants(
            self.impala_helpers,
            self.storage_config.impala.db,
            variants_table,
            pedigree_table,
            gene_models,
        )

        return family_variants

    def _generate_study_config(
            self, study_id, pedigree_table, variants_table=None):

        assert study_id is not None

        study_config = {
            "id": study_id,
            "conf_dir": ".",
            "has_denovo": False,
            "genotype_storage": {
                "id": self.storage_id,
                "tables": {"pedigree": pedigree_table},
            },
            "genotype_browser": {"enabled": False},
        }

        if variants_table:
            storage_config = study_config["genotype_storage"]
            storage_config["tables"]["variants"] = variants_table
            study_config["genotype_browser"]["enabled"] = True

        return study_config

    # pylint: disable=arguments-differ
    def simple_study_import(
            self,
            study_id,
            families_loader=None,
            variant_loaders=None,
            study_config=None,
            output=".",
            include_reference=False,
            **kwargs):

        variants_dir = None
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

                variants_dir = os.path.join(output, "variants")
                partition_description = NoPartitionDescriptor(variants_dir)

                ParquetManager.variants_to_parquet(
                    variant_loader,
                    partition_description,
                    # parquet_filenames.variants,
                    bucket_index=bucket_index,
                    include_reference=include_reference
                )

        pedigree_filename = os.path.join(
            output, "pedigree", "pedigree.parquet")
        families = families_loader.load()
        ParquetManager.families_to_parquet(
            families, pedigree_filename
        )

        config_dict = self.impala_load_dataset(
            study_id,
            variants_dir=variants_dir,
            pedigree_file=pedigree_filename
        )

        config_dict["has_denovo"] = has_denovo
        config_dict["has_cnv"] = has_cnv

        if study_config is not None:
            study_config_dict = GPFConfigParser.load_config_raw(study_config)
            config_dict = recursive_dict_update(config_dict, study_config_dict)

        config_builder = StudyConfigBuilder(config_dict)

        return config_builder.build_config()

    def default_hdfs_study_path(self, study_id):
        study_path = os.path.join(self.storage_config.hdfs.base_dir, study_id)
        # study_path = \
        #     f"hdfs://{self.storage_config.hdfs.host}:" \
        #     f"{self.storage_config.hdfs.port}{study_path}"
        return study_path

    def default_pedigree_hdfs_filename(self, study_id):
        study_path = self.default_hdfs_study_path(study_id)
        return os.path.join(study_path, "pedigree", "pedigree.parquet")

    def default_variants_hdfs_dirname(self, study_id):
        study_path = self.default_hdfs_study_path(study_id)
        return os.path.join(study_path, "variants")

    def full_hdfs_path(self, hdfs_path):
        result = \
            f"hdfs://{self.storage_config.hdfs.host}:" \
            f"{self.storage_config.hdfs.port}{hdfs_path}"
        return result

    def _build_hdfs_pedigree(
            self, study_id, pedigree_file):
        study_path = os.path.join(self.storage_config.hdfs.base_dir, study_id)
        hdfs_dir = os.path.join(study_path, "pedigree")
        basename = os.path.basename(pedigree_file)
        return os.path.join(hdfs_dir, basename)

    def _build_hdfs_variants(
            self, study_id, variants_dir, partition_description):
        study_path = os.path.join(self.storage_config.hdfs.base_dir, study_id)
        hdfs_variants_dir = os.path.join(study_path, "variants")

        files_glob = partition_description.generate_file_access_glob()
        files_glob = os.path.join(variants_dir, files_glob)
        local_variants_files = glob.glob(files_glob)
        # logger.debug(f"{variants_dir}, {files_glob}, {local_variants_files}")

        local_basedir = partition_description.variants_filename_basedir(
            local_variants_files[0])
        assert local_basedir.endswith("/")

        hdfs_variants_files = []
        for lvf in local_variants_files:
            assert lvf.startswith(local_basedir)
            hdfs_variants_files.append(
                os.path.join(hdfs_variants_dir, lvf[len(local_basedir):]))
        # logger.debug(f"{local_variants_files}, {hdfs_variants_files}")

        return local_variants_files, hdfs_variants_dir, hdfs_variants_files

    def _native_hdfs_upload_dataset(
            self, study_id, variants_dir,
            pedigree_file, partition_description):

        study_path = os.path.join(self.storage_config.hdfs.base_dir, study_id)
        pedigree_hdfs_path = os.path.join(
            study_path, "pedigree", "pedigree.parquet"
        )
        self.hdfs_helpers.put(pedigree_file, pedigree_hdfs_path)

        if variants_dir is None:
            return (None, None, pedigree_hdfs_path)

        local_variants_files, hdfs_variants_dir, hdfs_variants_files = \
            self._build_hdfs_variants(
                study_id, variants_dir, partition_description)

        partition_filename = os.path.join(
            variants_dir, "_PARTITION_DESCRIPTION")
        logger.debug(
            "checking for partition description: %s", partition_filename)
        if os.path.exists(partition_filename):
            logger.info(
                "copying partition description %s "
                "into %s", partition_filename, study_path)
            self.hdfs_helpers.put_in_directory(
                partition_filename, study_path)

        schema_filename = os.path.join(
            variants_dir, "_VARIANTS_SCHEMA")
        logger.debug(
            "checking for variants schema: %s", schema_filename)
        if os.path.exists(schema_filename):
            logger.info(
                "copying variants schema %s "
                "into %s", schema_filename, study_path)
            self.hdfs_helpers.put_in_directory(
                schema_filename, study_path)

        for lvf, hvf in zip(local_variants_files, hdfs_variants_files):
            hdfs_dir = os.path.dirname(hvf)
            self.hdfs_helpers.makedirs(hdfs_dir)
            self.hdfs_helpers.put_in_directory(lvf, hdfs_dir)

        return (hdfs_variants_dir, hdfs_variants_files[0], pedigree_hdfs_path)

    def _rsync_hdfs_upload_dataset(
            self, study_id, variants_dir,
            pedigree_file, partition_description):

        assert self.rsync_helpers is not None

        study_path = os.path.join(
            self.storage_config.hdfs.base_dir, study_id)
        if not study_path.endswith("/"):
            study_path += "/"
        self.rsync_helpers.clear_remote(study_path)

        partition_filename = os.path.join(
            variants_dir, "_PARTITION_DESCRIPTION")
        if os.path.exists(partition_filename):
            self.rsync_helpers.copy_to_remote(
                partition_filename, remote_subdir=study_path,
                clear_remote=False)

        schema_filename = os.path.join(
            variants_dir, "_VARIANTS_SCHEMA")
        if os.path.exists(schema_filename):
            self.rsync_helpers.copy_to_remote(
                schema_filename, remote_subdir=study_path,
                clear_remote=False)

        pedigree_rsync_path = os.path.join(
            study_path, "pedigree")
        self.rsync_helpers.copy_to_remote(
            pedigree_file, remote_subdir=pedigree_rsync_path)

        if variants_dir is None:
            return (
                None, None,
                self._build_hdfs_pedigree(study_id, pedigree_file))

        variants_rsync_path = os.path.join(
            study_path, "variants/")
        if not variants_dir.endswith("/"):
            variants_dir += "/"

        self.rsync_helpers.copy_to_remote(
            variants_dir, remote_subdir=variants_rsync_path,
            exclude=["_*"])

        _, hdfs_variants_dir, hdfs_variants_files = self._build_hdfs_variants(
            study_id, variants_dir, partition_description)
        # logger.debug(
        #     f"HDFS_VARIANTS_FILES: {hdfs_variants_dir}, "
        #     f"{hdfs_variants_files}")

        return (
            hdfs_variants_dir, hdfs_variants_files[0],
            self._build_hdfs_pedigree(study_id, pedigree_file))

    def hdfs_upload_dataset(
            self, study_id, variants_dir,
            pedigree_file, partition_description):
        """Upload a variants dir and pedigree file to hdfs."""
        if self.rsync_helpers is not None:
            return self._rsync_hdfs_upload_dataset(
                study_id, variants_dir,
                pedigree_file, partition_description)
        return self._native_hdfs_upload_dataset(
            study_id, variants_dir,
            pedigree_file, partition_description)

    def impala_import_dataset(
            self, study_id,
            pedigree_hdfs_file,
            variants_hdfs_dir,
            partition_description,
            variants_sample=None,
            variants_schema=None):
        """Create pedigree and variant tables for a study."""
        pedigree_table = self._construct_pedigree_table(study_id)
        variants_table = self._construct_variants_table(study_id)

        db = self.storage_config.impala.db

        self.impala_helpers.drop_table(db, variants_table)
        self.impala_helpers.drop_table(db, pedigree_table)

        self.impala_helpers.import_pedigree_into_db(
            db, pedigree_table, pedigree_hdfs_file)

        if variants_hdfs_dir is None:
            return self._generate_study_config(
                study_id, pedigree_table)

        assert variants_sample is not None or variants_schema is not None
        self.impala_helpers.import_variants_into_db(
            db, variants_table, variants_hdfs_dir,
            partition_description,
            variants_sample=variants_sample,
            variants_schema=variants_schema)

        return self._generate_study_config(
            study_id, pedigree_table, variants_table)

    def impala_load_dataset(self, study_id, variants_dir, pedigree_file):
        """Load a study data into impala genotype storage."""
        if variants_dir is None:
            partition_description = None
            variants_schema = None
        else:
            partition_config_file = os.path.join(
                variants_dir, "_PARTITION_DESCRIPTION"
            )
            if os.path.exists(partition_config_file):
                partition_description = ParquetPartitionDescriptor.from_config(
                    partition_config_file, root_dirname=variants_dir)
            else:
                partition_description = NoPartitionDescriptor(
                    root_dirname=variants_dir)

            variants_schema_file = os.path.join(
                variants_dir, "_VARIANTS_SCHEMA"
            )
            variants_schema = None
            if os.path.exists(variants_schema_file):
                with open(variants_schema_file, "rt") as infile:
                    content = infile.read()
                    schema = toml.loads(content)
                    variants_schema = schema["variants_schema"]

        variants_hdfs_dir, variants_hdfs_path, pedigree_hdfs_path = \
            self.hdfs_upload_dataset(
                study_id, variants_dir, pedigree_file, partition_description)

        return self.impala_import_dataset(
            study_id,
            pedigree_hdfs_path,
            variants_hdfs_dir,
            partition_description=partition_description,
            variants_schema=variants_schema,
            variants_sample=variants_hdfs_path)


STUDY_CONFIG_TEMPLATE = """
id = "{id}"
conf_dir = "."

[genotype_storage]
id = "{genotype_storage}"

[genotype_storage.tables]
pedigree = "{pedigree_table}"
variants = "{variants_table}"
"""
