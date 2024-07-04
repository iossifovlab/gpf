import logging
import os

from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.studies.dataset_helpers import DatasetHelpers
from impala_storage.schema1.impala_genotype_storage import ImpalaGenotypeStorage

logger = logging.getLogger(__name__)


class ImpalaDatasetHelpers(DatasetHelpers):
    """Helper class for work with studies in impala genotype storage."""

    def __init__(
        self, gpf_instance: GPFInstance | None = None,
    ) -> None:
        super().__init__(gpf_instance=gpf_instance)

    def is_impala_genotype_storage(self, dataset_id: str) -> bool:
        """Check if genotype storage is an impala genotype storage."""
        genotype_storage = self.get_genotype_storage(dataset_id)
        return "impala" in genotype_storage.get_storage_types()

    def check_dataset_hdfs_directories(
        self, genotype_storage: GenotypeStorage, dataset_id: str,
    ) -> bool:
        """Check if a dataset HDFS directories are OK.

        Works only for impala genotype storage.
        """
        # pylint: disable=too-many-return-statements
        logger.info(
            "genotype storage of study %s should be impala: %s",
            dataset_id, genotype_storage.get_storage_types())
        if "impala" not in genotype_storage.get_storage_types():
            return False

        assert isinstance(genotype_storage, ImpalaGenotypeStorage)
        impala_storage = genotype_storage

        hdfs_helpers = impala_storage.hdfs_helpers
        study_dir = impala_storage.default_hdfs_study_path(dataset_id)

        logger.info(
            "study hdfs dir %s should exists: %s",
            study_dir, hdfs_helpers.exists(study_dir))
        logger.info(
            "study hdfs dir %s should be a directory: %s",
            study_dir, hdfs_helpers.isdir(study_dir))

        if not hdfs_helpers.exists(study_dir) or \
                not hdfs_helpers.isdir(study_dir):
            return False

        pedigree_dir = os.path.join(study_dir, "pedigree")
        logger.info(
            "pedigree hdfs dir %s should exists: %s",
            pedigree_dir, hdfs_helpers.exists(pedigree_dir))
        logger.info(
            "pedigree hdfs dir %s should be a directory: %s",
            pedigree_dir, hdfs_helpers.isdir(pedigree_dir))

        if not hdfs_helpers.exists(pedigree_dir) or \
                not hdfs_helpers.isdir(pedigree_dir):
            return False

        pedigree_file = os.path.join(pedigree_dir, "pedigree.parquet")
        logger.info(
            "pedigree hdfs file %s should exists: %s",
            pedigree_file, hdfs_helpers.exists(pedigree_file))
        logger.info(
            "pedigree hdfs file %s should be a file: %s",
            pedigree_file, hdfs_helpers.isfile(pedigree_file))

        if not hdfs_helpers.exists(pedigree_file) or \
                not hdfs_helpers.isfile(pedigree_file):
            return False
        config = self.find_genotype_data_config(dataset_id)
        if config is None:
            return True

        variants_table = config.genotype_storage.tables.variants
        if variants_table is None:
            logger.info(
                "dataset %s does not have variants; skipping checks for "
                "variants directory...", dataset_id)
        else:
            variants_dir = os.path.join(study_dir, "variants")
            logger.info(
                "variants hdfs dir %s should exists: %s",
                variants_dir, hdfs_helpers.exists(variants_dir))
            logger.info(
                "variants hdfs dir %s should be a directory: %s",
                variants_dir, hdfs_helpers.isdir(variants_dir))
            if not hdfs_helpers.exists(variants_dir) or \
                    not hdfs_helpers.isdir(variants_dir):
                return False

        return True

    def check_dataset_rename_hdfs_directory(
        self, old_id: str, new_id: str,
    ) -> tuple[str | None, str | None]:
        """Check if it is OK to rename an HDFS directory for a dataset.

        Works for impala genotype storage.
        """
        genotype_storage = self.get_genotype_storage(old_id)
        assert isinstance(genotype_storage, ImpalaGenotypeStorage)

        if not self.check_dataset_hdfs_directories(genotype_storage, old_id):
            return (None, None)

        hdfs_helpers = genotype_storage.hdfs_helpers

        source_dir = genotype_storage.default_hdfs_study_path(old_id)
        dest_dir = genotype_storage.default_hdfs_study_path(new_id)

        logger.info(
            "source hdfs dir %s should exists: %s",
            source_dir, hdfs_helpers.exists(source_dir))

        logger.info(
            "source hdfs dir %s should be a directory: %s",
            source_dir, hdfs_helpers.isdir(source_dir))

        logger.info(
            "destination hdfs dir %s should not exists: %s",
            dest_dir, not hdfs_helpers.exists(dest_dir))

        if hdfs_helpers.exists(source_dir) and \
                hdfs_helpers.isdir(source_dir) and \
                not hdfs_helpers.exists(dest_dir):
            return (source_dir, dest_dir)

        return (None, None)

    def dataset_rename_hdfs_directory(
        self, old_id: str, new_id: str, dry_run: bool = False,
    ) -> None:
        """Rename dataset HDFS directory."""
        source_dir, dest_dir = \
            self.check_dataset_rename_hdfs_directory(old_id, new_id)
        if not dry_run:
            assert (source_dir is not None) and (dest_dir is not None), (
                old_id, new_id)

        genotype_storage = self.get_genotype_storage(old_id)
        hdfs_helpers = genotype_storage.hdfs_helpers

        logger.info("going to rename %s to %s", source_dir, dest_dir)
        if not dry_run:
            hdfs_helpers.rename(source_dir, dest_dir)

    def dataset_remove_hdfs_directory(
        self, dataset_id: str, dry_run: bool = False,
    ) -> None:
        """Remove dataset HDFS directory."""
        genotype_storage = self.get_genotype_storage(dataset_id)
        assert self.check_dataset_hdfs_directories(
            genotype_storage, dataset_id)

        hdfs_helpers = genotype_storage.hdfs_helpers

        study_dir = genotype_storage.default_hdfs_study_path(dataset_id)

        logger.info("going to remove HDFS directory: %s", study_dir)
        if not dry_run:
            hdfs_helpers.delete(study_dir, recursive=True)

    def dataset_recreate_impala_tables(
        self, old_id: str, new_id: str, dry_run: bool = False,
    ) -> tuple[str, str | None]:
        """Recreate impala tables for a dataset."""
        genotype_storage = self.get_genotype_storage(old_id)

        assert genotype_storage.storage_type == "impala"
        if not dry_run:
            assert self.check_dataset_hdfs_directories(
                genotype_storage, new_id)

        impala_db = genotype_storage.storage_config.impala.db
        impala_helpers = genotype_storage.impala_helpers

        new_hdfs_pedigree = genotype_storage \
            .default_pedigree_hdfs_filename(new_id)
        new_hdfs_pedigree = os.path.dirname(new_hdfs_pedigree)
        # pylint: disable=protected-access
        new_pedigree_table = genotype_storage._construct_pedigree_table(new_id)

        config = self.find_genotype_data_config(old_id)

        pedigree_table = config.genotype_storage.tables.pedigree

        logger.info(
            "going to recreate pedigree table %s from %s",
            new_pedigree_table, new_hdfs_pedigree)
        if not dry_run:
            impala_helpers.recreate_table(
                impala_db, pedigree_table,
                new_pedigree_table, new_hdfs_pedigree)

        variants_table = config.genotype_storage.tables.variants
        new_variants_table = None

        if variants_table is not None:
            new_hdfs_variants = genotype_storage \
                .default_variants_hdfs_dirname(new_id)

            # pylint: disable=protected-access
            new_variants_table = genotype_storage \
                ._construct_variants_table(new_id)

            logger.info(
                "going to recreate variants table %s from %s",
                new_variants_table, new_hdfs_variants)

            if not dry_run:
                impala_helpers.recreate_table(
                    impala_db, variants_table,
                    new_variants_table, new_hdfs_variants)

        return new_pedigree_table, new_variants_table

    def dataset_drop_impala_tables(
        self, dataset_id: str, dry_run: bool = False,
    ) -> None:
        """Drop impala tables for a dataset."""
        assert self.check_dataset_impala_tables(dataset_id)

        genotype_storage = self.get_genotype_storage(dataset_id)

        impala_db = genotype_storage.storage_config.impala.db
        impala_helpers = genotype_storage.impala_helpers

        config = self.find_genotype_data_config(dataset_id)

        pedigree_table = config.genotype_storage.tables.pedigree
        logger.info(
            "going to drop pedigree impala table %s.%s",
            impala_db, pedigree_table)
        if not dry_run:
            impala_helpers.drop_table(
                impala_db, pedigree_table)

        variants_table = config.genotype_storage.tables.variants
        if variants_table is not None:
            logger.info(
                "going to drop variants impala table %s.%s",
                impala_db, pedigree_table)
            if not dry_run:
                impala_helpers.drop_table(
                    impala_db, variants_table)

    def check_dataset_impala_tables(self, dataset_id: str) -> bool:
        """Check if impala tables for a dataset are OK."""
        genotype_storage = self.get_genotype_storage(dataset_id)

        impala_db = genotype_storage.storage_config.impala.db
        impala_helpers = genotype_storage.impala_helpers

        config = self.find_genotype_data_config(dataset_id)

        pedigree_table = config.genotype_storage.tables.pedigree

        logger.info(
            "impala pedigree table %s.%s should exists: %s",
            impala_db, pedigree_table,
            impala_helpers.check_table(impala_db, pedigree_table))

        if not impala_helpers.check_table(impala_db, pedigree_table):
            return False

        create_statement = impala_helpers.get_table_create_statement(
            impala_db, pedigree_table)

        logger.info(
            "pedigree table %s.%s should be external table: "
            "'CREATE EXTERNAL TABLE' in %s",
            impala_db, pedigree_table, create_statement)
        if "CREATE EXTERNAL TABLE" not in create_statement:
            return False

        variants_table = config.genotype_storage.tables.variants
        if variants_table is None:
            logger.info(
                "dataset %s has no variants; skipping checks for variants "
                "table", dataset_id)
        else:
            logger.info(
                "impala variants table %s.%s should exists: %s",
                impala_db, variants_table,
                impala_helpers.check_table(impala_db, variants_table),
            )
            if not impala_helpers.check_table(impala_db, variants_table):
                return False

            create_statement = impala_helpers.get_table_create_statement(
                impala_db, variants_table)

            logger.info(
                "variants table %s.%s should be external table: "
                "'CREATE EXTERNAL TABLE' in %s",
                impala_db, variants_table, create_statement,
            )
            if "CREATE EXTERNAL TABLE" not in create_statement:
                return False

        return True
