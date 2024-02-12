from __future__ import annotations

import os
import glob
import logging
from typing import Any, cast, Optional

import toml
from cerberus import Validator
from box import Box

from dae.configuration.utils import validate_path
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.genomic_resources.gene_models import GeneModels
from dae.genomic_resources.reference_genome import ReferenceGenome

from impala_storage.helpers.hdfs_helpers import HdfsHelpers
from impala_storage.helpers.impala_helpers import ImpalaHelpers
from impala_storage.schema1.impala_variants import ImpalaVariants
from impala_storage.schema1.utils import generate_file_access_glob, \
    variants_filename_basedir

from impala_storage.helpers.rsync_helpers import RsyncHelpers


logger = logging.getLogger(__name__)


class ImpalaGenotypeStorage(GenotypeStorage):
    """Defines Apache Impala genotype storage."""

    VALIDATION_SCHEMA = {
        "storage_type": {"type": "string", "allowed": ["impala"]},
        "id": {
            "type": "string",
        },
        "impala": {
            "type": "dict",
            "schema": {
                "hosts": {
                    "type": "list",
                    "schema": {"type": "string"},
                    "required": True,
                },
                "port": {"type": "integer", "default": 21050},
                "db": {"type": "string", "required": True},
                "pool_size": {"type": "integer", "default": 1}
            },
            "required": True,
        },
        "hdfs": {
            "type": "dict",
            "schema": {
                "host": {"type": "string", "required": True},
                "port": {"type": "integer", "default": 8020},
                "replication": {"type": "integer", "default": 1},
                "base_dir": {
                    "type": "string",
                    "check_with": validate_path,
                    "required": True,
                },
            },
            "required": True,
        },
        "rsync": {
            "type": "dict",
            "schema": {
                "location": {"type": "string"},
                "remote_shell": {
                    "type": "string",
                    "default": None,
                    "nullable": True
                },
            },
            "nullable": True,
        }
    }

    def __init__(self, storage_config: dict[str, Any]) -> None:
        super().__init__(storage_config)

        self._impala_helpers: Optional[ImpalaHelpers] = None

        self._hdfs_helpers: Optional[HdfsHelpers] = None
        self._rsync_helpers: Optional[RsyncHelpers] = None

    @classmethod
    def validate_and_normalize_config(cls, config: dict) -> dict:
        config = super().validate_and_normalize_config(config)
        validator = Validator(cls.VALIDATION_SCHEMA)
        if not validator.validate(config):
            logger.error(
                "wrong config format for impala genotype storage: %s",
                validator.errors)
            raise ValueError(
                f"wrong config format for impala storage: "
                f"{validator.errors}")
        return cast(dict, validator.document)

    @classmethod
    def get_storage_types(cls) -> set[str]:
        return {"impala"}

    def start(self) -> ImpalaGenotypeStorage:
        return self

    def shutdown(self) -> ImpalaGenotypeStorage:
        if self._hdfs_helpers is not None:
            self._hdfs_helpers.close()
        if self._impala_helpers is not None:
            self._impala_helpers.close()
        return self

    def get_db(self) -> str:
        return cast(str, self.storage_config["impala"]["db"])

    @property
    def impala_helpers(self) -> ImpalaHelpers:
        """Return an impala helper object."""
        if self._impala_helpers is None:
            impala_hosts = self.storage_config["impala"]["hosts"]
            impala_port = self.storage_config["impala"]["port"]
            pool_size = self.storage_config["impala"]["pool_size"]

            self._impala_helpers = ImpalaHelpers(
                impala_hosts=impala_hosts, impala_port=impala_port,
                pool_size=pool_size)

        return self._impala_helpers

    @property
    def hdfs_helpers(self) -> HdfsHelpers:
        """Create and return an HDFS helpers object."""
        if self._hdfs_helpers is None:
            self._hdfs_helpers = HdfsHelpers(
                self.storage_config["hdfs"]["host"],
                self.storage_config["hdfs"]["port"],
                replication=self.storage_config["hdfs"]["replication"]
            )

        assert self._hdfs_helpers is not None
        return self._hdfs_helpers

    @property
    def rsync_helpers(self) -> Optional[RsyncHelpers]:
        if self._rsync_helpers is None and self.storage_config.get("rsync"):
            self._rsync_helpers = RsyncHelpers(
                self.storage_config["rsync"]["location"]
            )
        return self._rsync_helpers

    @classmethod
    def study_tables(
        cls, study_config: dict[str, Any]
    ) -> tuple[str, str]:
        """Return variants and pedigree tables names for a study."""
        storage_config = cast(Box, study_config).genotype_storage
        study_id = cast(Box, study_config).id
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
            variants_table = cls._construct_variants_table(study_id)
            pedigree_table = cls._construct_pedigree_table(study_id)
        return variants_table, pedigree_table

    @staticmethod
    def _construct_variants_table(study_id: str) -> str:
        return f"{study_id}_variants"

    @staticmethod
    def _construct_pedigree_table(study_id: str) -> str:
        return f"{study_id}_pedigree"

    def build_backend(
        self, study_config: dict[str, Any],
        genome: ReferenceGenome,
        gene_models: GeneModels
    ) -> ImpalaVariants:
        assert study_config is not None

        variants_table, pedigree_table = self.study_tables(study_config)
        family_variants = ImpalaVariants(
            self.impala_helpers,
            self.storage_config["impala"]["db"],
            variants_table,
            pedigree_table,
            gene_models,
        )

        return family_variants

    def _generate_study_config(
        self, study_id: str,
        pedigree_table: str,
        variants_table: Optional[str] = None
    ) -> dict[str, Any]:

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
            storage_config = cast(
                dict[str, Any],
                study_config["genotype_storage"])
            storage_config["tables"]["variants"] = variants_table
            study_config["genotype_browser"]["enabled"] = True  # type: ignore

        return study_config

    def default_hdfs_study_path(self, study_id: str) -> str:
        study_path = os.path.join(
            self.storage_config["hdfs"]["base_dir"], study_id)
        return study_path

    def default_pedigree_hdfs_filename(self, study_id: str) -> str:
        study_path = self.default_hdfs_study_path(study_id)
        return os.path.join(study_path, "pedigree", "pedigree.parquet")

    def default_variants_hdfs_dirname(self, study_id: str) -> str:
        study_path = self.default_hdfs_study_path(study_id)
        return os.path.join(study_path, "variants")

    def _build_hdfs_pedigree(
            self, study_id: str, pedigree_file: str) -> str:
        study_path = os.path.join(
            self.storage_config["hdfs"]["base_dir"], study_id)
        hdfs_dir = os.path.join(study_path, "pedigree")
        basename = os.path.basename(pedigree_file)
        return os.path.join(hdfs_dir, basename)

    def _build_hdfs_variants(
        self, study_id: str,
        variants_dir: str,
        partition_description: PartitionDescriptor
    ) -> tuple[list[str], str, list[str]]:
        study_path = os.path.join(
            self.storage_config["hdfs"]["base_dir"], study_id)
        hdfs_variants_dir = os.path.join(study_path, "variants")

        files_glob = generate_file_access_glob(partition_description)
        files_glob = os.path.join(variants_dir, files_glob)
        local_variants_files = glob.glob(files_glob)
        # logger.debug(f"{variants_dir}, {files_glob}, {local_variants_files}")

        local_basedir = variants_filename_basedir(
            partition_description,
            local_variants_files[0])
        assert local_basedir is not None
        assert local_basedir.endswith("/")

        hdfs_variants_files = []
        for lvf in local_variants_files:
            assert lvf.startswith(local_basedir)
            hdfs_variants_files.append(
                os.path.join(hdfs_variants_dir, lvf[len(local_basedir):]))
        # logger.debug(f"{local_variants_files}, {hdfs_variants_files}")

        return local_variants_files, hdfs_variants_dir, hdfs_variants_files

    def _native_hdfs_upload_dataset(
        self, study_id: str, variants_dir: str,
        pedigree_file: str, partition_description: PartitionDescriptor
    ) -> tuple[str, str, str]:

        study_path = os.path.join(
            self.storage_config["hdfs"]["base_dir"], study_id)
        if self.hdfs_helpers.exists(study_path):
            self.hdfs_helpers.delete(study_path, recursive=True)

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
        self, study_id: str, variants_dir: str,
        pedigree_file: str,
        partition_description: PartitionDescriptor
    ) -> tuple[str, str, str]:

        assert self.rsync_helpers is not None

        study_path = os.path.join(
            self.storage_config["hdfs"]["base_dir"], study_id)
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
        self, study_id: str, variants_dir: str,
        pedigree_file: str,
        partition_description: PartitionDescriptor
    ) -> tuple[str, str, str]:
        """Upload a variants dir and pedigree file to hdfs."""
        if self.rsync_helpers is not None:
            return self._rsync_hdfs_upload_dataset(
                study_id, variants_dir,
                pedigree_file, partition_description)
        return self._native_hdfs_upload_dataset(
            study_id, variants_dir,
            pedigree_file, partition_description)

    def impala_import_dataset(
        self, study_id: str,
        pedigree_hdfs_file: str,
        variants_hdfs_dir: str,
        partition_description: PartitionDescriptor,
        variants_sample: Optional[str] = None,
        variants_schema: Optional[dict[str, str]] = None
    ) -> dict[str, Any]:
        """Create pedigree and variant tables for a study."""
        pedigree_table = self._construct_pedigree_table(study_id)
        variants_table = self._construct_variants_table(study_id)

        db = self.storage_config["impala"]["db"]

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

    def impala_load_dataset(
        self, study_id: str, variants_dir: str,
        pedigree_file: str
    ) -> dict[str, Any]:
        """Load a study data into impala genotype storage."""
        if variants_dir is None:
            partition_description = None
            variants_schema = None
        else:
            partition_config_file = os.path.join(
                variants_dir, "_PARTITION_DESCRIPTION"
            )
            if os.path.exists(partition_config_file):
                partition_description = PartitionDescriptor.parse(
                    partition_config_file)
            else:
                partition_description = PartitionDescriptor()

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
