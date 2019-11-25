import os
import sys
from time import time

from dae.backends.storage.genotype_storage import GenotypeStorage

from dae.backends.impala.hdfs_helpers import HdfsHelpers
from dae.backends.impala.impala_helpers import ImpalaHelpers
from dae.backends.impala.impala_variants import ImpalaFamilyVariants
from dae.backends.impala.parquet_io import ParquetManager


class ImpalaGenotypeStorage(GenotypeStorage):

    def __init__(self, storage_config):
        super(ImpalaGenotypeStorage, self).__init__(storage_config)

        self._impala_connection = None
        self._impala_helpers = None
        self._hdfs_helpers = None

    def get_db(self):
        return self.storage_config.impala.db

    def is_impala(self):
        return True

    def get_hdfs_dir(self, *path):
        hdfs_dirname = os.path.join(
            self.storage_config.hdfs.base_dir, *path
        )
        if not self.hdfs_helpers.hdfs.exists(hdfs_dirname):
            self.hdfs_helpers.hdfs.mkdir(hdfs_dirname)

        return hdfs_dirname

    @property
    def impala_connection(self):
        if self._impala_connection is None:
            self._impala_connection = ImpalaHelpers.create_impala_connection(
                self.storage_config.impala.host,
                self.storage_config.impala.port
            )

        return self._impala_connection

    @property
    def impala_helpers(self):
        if self._impala_helpers is None:
            self._impala_helpers = ImpalaHelpers(
                impala_connection=self.impala_connection
            )

        return self._impala_helpers

    @property
    def hdfs_helpers(self):
        if self._hdfs_helpers is None:
            self._hdfs_helpers = HdfsHelpers(
                self.storage_config.hdfs.host,
                self.storage_config.hdfs.port
            )

        return self._hdfs_helpers

    @staticmethod
    def study_tables(study_config):
        if study_config.tables and \
                study_config.tables.pedigree and study_config.tables.variant:
            variant_table = study_config.tables.variant
            pedigree_table = study_config.tables.pedigree
        else:
            # default study tables
            variant_table = '{}_variant'.format(study_config.id)
            pedigree_table = '{}_pedigree'.format(study_config.id)
        return variant_table, pedigree_table

    def build_backend(self, study_config, genomes_db):
        variant_table, pedigree_table = self.study_tables(study_config)

        family_variants = ImpalaFamilyVariants(
            self.impala_connection,
            self.storage_config.impala.db,
            variant_table, pedigree_table,
            genomes_db.get_gene_models()
        )

        return family_variants

    def impala_load_study(self, study_id, variant_paths, pedigree_paths):
        variant_hdfs_path, pedigree_hdfs_path = \
            self._hdfs_parquet_put_study_files(
                study_id, variant_paths, pedigree_paths)

        db = self.storage_config.impala.db
        pedigree_table = '{}_pedigree'.format(study_id)
        variant_table = '{}_variant'.format(study_id)

        print(
            f'Loading `{study_id}` study in impala '
            f'`{db}` db; '
            f'variants from {variant_paths}; '
            f'pedigrees from {pedigree_paths}', file=sys.stderr
        )
        start = time()
        self.impala_helpers.import_variants(
            db,
            variant_table, pedigree_table,
            variant_hdfs_path, pedigree_hdfs_path)

        end = time()
        total = end - start
        print(
            f'Loaded `{study_id}` study in impala `{db}` '
            f'db for {total:.2f} sec', file=sys.stderr
        )
        return self._generate_study_config(
            study_id, variant_table, pedigree_table)

    def _hdfs_parquet_put_study_files(
            self, study_id, variant_paths, pedigree_paths):
        print("pedigree_path:", pedigree_paths)
        print("variants_path:", variant_paths)
        pedigree_dirname = self.get_hdfs_dir(study_id, 'pedigree')
        variants_dirname = self.get_hdfs_dir(study_id, 'variants')

        for pedigree_path in pedigree_paths:
            self.hdfs_helpers.put_content(pedigree_path, pedigree_dirname)
        for variant_path in variant_paths:
            self.hdfs_helpers.put_content(variant_path, variants_dirname)

        pedigree_files = self.hdfs_helpers.list_dir(pedigree_dirname)
        variant_files = self.hdfs_helpers.list_dir(variants_dirname)

        return variant_files, pedigree_files

    def _generate_study_config(self, study_id, variant_table, pedigree_table):
        assert study_id is not None

        study_config = STUDY_CONFIG_TEMPLATE.format(
                id=study_id,
                genotype_storage=self.id,
                pedigree_table=pedigree_table,
                variant_table=variant_table)
        return study_config

    def simple_study_import(
            self, study_id, denovo_loader, vcf_loader,
            families_loader, output='.'):

        assert denovo_loader is not None or vcf_loader is not None

        parquet_pedigrees = []
        parquet_variants = []

        parquet_filenames = None
        if vcf_loader is not None:
            bucket_index = 100  # transmitted buckets (>=100)
            parquet_filenames = ParquetManager.build_parquet_filenames(
                output, bucket_index=bucket_index, study_id=study_id
            )
            ParquetManager.variants_to_parquet(
                vcf_loader, parquet_filenames.variant,
                bucket_index=bucket_index,
                filesystem=None
            )
            parquet_variants.append(parquet_filenames.variant)

        if denovo_loader is not None:
            bucket_index = 0  # denovo buckets (0-99)
            parquet_filenames = ParquetManager.build_parquet_filenames(
                output, bucket_index=bucket_index, study_id=study_id
            )
            ParquetManager.variants_to_parquet(
                denovo_loader, parquet_filenames.variant,
                bucket_index=bucket_index,
                filesystem=None
            )
            parquet_variants.append(parquet_filenames.variant)

        assert parquet_filenames is not None
        print("families save in:", parquet_filenames)
        ParquetManager.families_loader_to_parquet(
            families_loader, parquet_filenames.pedigree
        )

        parquet_pedigrees.append(parquet_filenames.pedigree)

        return self.impala_load_study(
            study_id, parquet_variants, parquet_pedigrees)


STUDY_CONFIG_TEMPLATE = '''
[study]

id = {id}
genotype_storage = {genotype_storage}
tables = pedigree:{pedigree_table},
    variant:{variant_table}

'''
