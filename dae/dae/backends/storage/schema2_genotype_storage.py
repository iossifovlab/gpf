import glob
from itertools import chain
import os
import logging
from dataclasses import dataclass
from collections.abc import Iterator
from dae.backends.impala.hdfs_helpers import HdfsHelpers
from dae.backends.impala.impala_helpers import ImpalaHelpers
from dae.backends.schema2.impala_variants import ImpalaVariants
from dae.backends.storage.genotype_storage import GenotypeStorage


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class HdfsStudyLayout:
    pedigree_file: str
    summary_variant_dir: str
    family_variant_dir: str
    summary_sample: str
    family_sample: str
    meta_file: str


class Schema2GenotypeStorage(GenotypeStorage):
    """A genotype storing implementing the new schema2."""

    def __init__(self, storage_config, section_id):
        super().__init__(storage_config, section_id)
        self._hdfs_helpers = None

        impala_hosts = self.storage_config.impala.hosts
        impala_port = self.storage_config.impala.port
        pool_size = self.storage_config.impala.pool_size

        self._impala_helpers = ImpalaHelpers(
            impala_hosts=impala_hosts, impala_port=impala_port,
            pool_size=pool_size)

    def is_impala(self):
        return False

    def is_filestorage(self):
        return False

    def build_backend(self, study_id, genome, gene_models):
        assert study_id is not None

        family_table, summary_table, pedigree_table, meta_table \
            = self._study_tables(study_id)
        variants = ImpalaVariants(
            self.impala_helpers,
            self.storage_config.impala.db,
            family_table,
            summary_table,
            pedigree_table,
            meta_table,
            gene_models,
        )
        # TODO create a bigquery variants if so specified in the config
        return variants

    def simple_study_import(
        self,
        study_id,
        families_loader=None,
        variant_loaders=None,
        study_config=None,
        **kwargs,
    ):
        raise NotImplementedError()

    def hdfs_upload_dataset(self, study_id, variants_dir, pedigree_file,
                            meta_file, partition_description) \
            -> HdfsStudyLayout:
        """Upload local data to hdfs."""
        # Copy pedigree
        study_path = os.path.join(self.storage_config.hdfs.base_dir, study_id)
        pedigree_hdfs_path = os.path.join(
            study_path, "pedigree", "pedigree.parquet"
        )
        self.hdfs_helpers.put(pedigree_file, pedigree_hdfs_path)

        meta_hdfs_file = os.path.join(
            study_path, "meta", "meta.parquet"
        )
        self.hdfs_helpers.put(meta_file, meta_hdfs_file)

        # Copy optional files
        optional_files = [
            "_PARTITION_DESCRIPTION",
            "_VARIANTS_SCHEMA",
        ]
        for optional_file in optional_files:
            optional_filename = os.path.join(variants_dir, optional_file)
            logger.debug("checking for: %s", optional_filename)
            if os.path.exists(optional_filename):
                logger.info("copying %s into %s",
                            optional_filename, study_path)
                self.hdfs_helpers.put_in_directory(optional_filename,
                                                   study_path)

        # Copy variants if any
        summary_sample_hdfs_file, family_sample_hdfs_file = \
            self._copy_variants(variants_dir, partition_description,
                                study_path)

        return HdfsStudyLayout(
            pedigree_file=pedigree_hdfs_path,
            summary_variant_dir=os.path.join(study_path, "summary"),
            family_variant_dir=os.path.join(study_path, "family"),
            summary_sample=summary_sample_hdfs_file,
            family_sample=family_sample_hdfs_file,
            meta_file=meta_hdfs_file,
        )

    @staticmethod
    def _study_tables(study_config) -> tuple[str, str, str, str]:
        study_id = study_config.id
        storage_config = study_config.genotype_storage
        has_tables = storage_config and storage_config.tables
        tables = storage_config.tables if has_tables else None

        family_table = f"{study_id}_family_alleles"
        if has_tables and tables.family:
            family_table = tables.family

        summary_table = f"{study_id}_summary_alleles"
        if has_tables and tables.summary:
            summary_table = tables.summary

        pedigree_table = f"{study_id}_pedigree"
        if has_tables and tables.pedigree:
            pedigree_table = tables.pedigree

        meta_table = f"{study_id}_meta"
        if has_tables and tables.meta:
            meta_table = tables.meta

        return family_table, summary_table, pedigree_table, meta_table

    def _copy_variants(self, variants_dir, partition_description, study_path):
        hdfs_summary_dir = os.path.join(study_path, "summary")
        hdfs_family_dir = os.path.join(study_path, "family")

        assert variants_dir == partition_description.output
        # TODO why pass variants_dir as a independant input parameter ?

        src_summary_dir = os.path.join(
            variants_dir, partition_description.summary_alleles_dirname)
        src_family_dir = os.path.join(
            variants_dir, partition_description.family_alleles_dirname)

        summary_files_to_copy = list(self._enum_parquet_files_to_copy(
            src_summary_dir, hdfs_summary_dir))
        family_files_to_copy = list(self._enum_parquet_files_to_copy(
            src_family_dir, hdfs_family_dir))
        for src_file, hdfs_file in chain(summary_files_to_copy,
                                         family_files_to_copy):
            hdfs_dir = os.path.dirname(hdfs_file)
            self.hdfs_helpers.makedirs(hdfs_dir)
            self.hdfs_helpers.put_in_directory(src_file, hdfs_dir)

        # return the first parquet files in the list as sample files
        return summary_files_to_copy[0][1], family_files_to_copy[0][1]

    @staticmethod
    def _enum_parquet_files_to_copy(src_variants_dir, dest_dir) \
            -> Iterator[tuple[str, str]]:
        parquet_files_glob = glob.iglob(
            os.path.join(src_variants_dir, "**/*.parquet"),
            recursive=True)

        for src_file in parquet_files_glob:
            dst_file = os.path.join(dest_dir,
                                    src_file[len(src_variants_dir) + 1:])
            yield src_file, dst_file

    @property
    def hdfs_helpers(self):
        """Return the hdfs helper used to interact with hdfs."""
        if self._hdfs_helpers is None:
            self._hdfs_helpers = HdfsHelpers(
                self.storage_config.hdfs.host,
                self.storage_config.hdfs.port,
                replication=self.storage_config.hdfs.replication
            )

        return self._hdfs_helpers

    def import_dataset(
            self, study_id,
            hdfs_study_layout: HdfsStudyLayout,
            partition_description):
        """Load a dataset from HDFS into impala."""
        pedigree_table = self._construct_pedigree_table(study_id)
        summary_variant_table, family_variant_table = \
            self._construct_variant_tables(study_id)
        meta_table = self._construct_metadata_table(study_id)

        db = self.storage_config.impala.db

        self.impala_helpers.drop_table(db, summary_variant_table)
        self.impala_helpers.drop_table(db, family_variant_table)
        self.impala_helpers.drop_table(db, pedigree_table)
        self.impala_helpers.drop_table(db, meta_table)

        self.impala_helpers.import_pedigree_into_db(
            db, pedigree_table, hdfs_study_layout.pedigree_file)

        self.impala_helpers.import_pedigree_into_db(
            db, meta_table, hdfs_study_layout.meta_file)

        assert hdfs_study_layout.summary_sample is not None
        self.impala_helpers.import_variants_into_db(
            db, summary_variant_table, hdfs_study_layout.summary_variant_dir,
            partition_description,
            variants_sample=hdfs_study_layout.summary_sample)

        assert hdfs_study_layout.family_sample is not None
        self.impala_helpers.import_variants_into_db(
            db, family_variant_table, hdfs_study_layout.family_variant_dir,
            partition_description,
            variants_sample=hdfs_study_layout.family_sample)

        return self._generate_study_config(
            study_id, pedigree_table,
            summary_variant_table, family_variant_table, meta_table)

    @property
    def impala_helpers(self):
        assert self._impala_helpers is not None
        return self._impala_helpers

    @staticmethod
    def _construct_variant_tables(study_id):
        return f"{study_id}_summary_alleles", f"{study_id}_family_alleles"

    @staticmethod
    def _construct_pedigree_table(study_id):
        return f"{study_id}_pedigree"

    @staticmethod
    def _construct_metadata_table(study_id):
        return f"{study_id}_meta"

    def _generate_study_config(self, study_id, pedigree_table,
                               summary_table, family_table, meta_table):

        assert study_id is not None

        study_config = {
            "id": study_id,
            "conf_dir": ".",
            "has_denovo": False,
            "genotype_storage": {
                "id": self.id,
                "tables": {"pedigree": pedigree_table},
            },
            "genotype_browser": {"enabled": False},
        }

        if summary_table:
            assert family_table is not None
            storage_config = study_config["genotype_storage"]
            storage_config["tables"]["summary"] = summary_table
            storage_config["tables"]["family"] = family_table
            storage_config["tables"]["meta"] = meta_table
            study_config["genotype_browser"]["enabled"] = True

        return study_config