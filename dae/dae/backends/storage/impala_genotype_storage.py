import os
import sys
import glob
from time import time

from dae.backends.raw.loader import VariantsLoader, TransmissionType
from dae.backends.storage.genotype_storage import GenotypeStorage

from dae.backends.impala.hdfs_helpers import HdfsHelpers
from dae.backends.impala.impala_helpers import ImpalaHelpers
from dae.backends.impala.impala_variants import ImpalaFamilyVariants
from dae.backends.impala.parquet_io import ParquetManager, \
    ParquetPartitionDescription


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

    def impala_drop_study_tables(self, study_config):
        for table in self.study_tables(study_config):
            self.impala_helpers.drop_table(
                self.get_db(), table
            )

    def impala_load_study(
            self, study_id,
            variant_paths=[],
            pedigree_paths=[]):
        assert variant_paths
        assert pedigree_paths

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

    def _hdfs_parquet_put_files(self, study_id, paths, dirname):
        hdfs_dirname = self.get_hdfs_dir(study_id, dirname)

        for path in paths:
            self.hdfs_helpers.put_content(path, hdfs_dirname)

        return self.hdfs_helpers.list_dir(hdfs_dirname)

    def _hdfs_parquet_put_study_files(
            self, study_id, variant_paths, pedigree_paths):
        print("pedigree_path:", pedigree_paths)
        print("variants_path:", variant_paths)

        pedigree_files = self._hdfs_parquet_put_files(
                study_id,
                pedigree_paths,
                'pedigree')

        variant_files = self._hdfs_parquet_put_files(
                study_id,
                variant_paths,
                'variants')

        return variant_files, pedigree_files

    def _generate_study_config(self, study_id, variant_table, pedigree_table):
        assert study_id is not None

        study_config = STUDY_CONFIG_TEMPLATE.format(
                id=study_id,
                genotype_storage=self.id,
                pedigree_table=pedigree_table,
                variant_table=variant_table)
        return study_config

    def _put_partition_file(self, filename, hdfs_path):
        self.hdfs_helpers.makedirs(hdfs_path)
        self.hdfs_helpers.put_in_directory(filename, hdfs_path)

    def simple_study_import(
            self, study_id,
            families_loader=None,
            variant_loaders=None,
            output='.'):

        parquet_pedigrees = []
        parquet_variants = []

        parquet_filenames = None
        for index, variant_loader in enumerate(variant_loaders):
            assert isinstance(variant_loader, VariantsLoader), \
                type(variant_loader)

            if variant_loader.transmission_type == TransmissionType.denovo:
                assert index < 100

                bucket_index = index  # denovo buckets < 100
            elif variant_loader.transmission_type == \
                    TransmissionType.transmitted:
                bucket_index = index + 100  # transmitted buckets (>=100)

            parquet_filenames = ParquetManager.build_parquet_filenames(
                output, bucket_index=bucket_index, study_id=study_id
            )
            ParquetManager.variants_to_parquet(
                variant_loader, parquet_filenames.variant,
                bucket_index=bucket_index,
                filesystem=None
            )
            parquet_variants.append(parquet_filenames.variant)

        assert parquet_filenames is not None
        print("families save in:", parquet_filenames)
        families = families_loader.load()

        ParquetManager.families_loader_to_parquet(
            families, parquet_filenames.pedigree
        )

        parquet_pedigrees.append(parquet_filenames.pedigree)

        return self.impala_load_study(
            study_id,
            variant_paths=parquet_variants,
            pedigree_paths=parquet_pedigrees)

    def impala_load_dataset(
            self, study_id, partition_description, pedigree_file,
            db, partition_hdfs_path, files):
        partition_table = f'{study_id}_partition'
        pedigree_table = f'{study_id}_pedigree'

        print(
            f'Loading partition with study_id `{study_id}` in impala '
            f'in db {db};'
        )

        start = time()

        self.impala_helpers.import_dataset_into_db(
            db,
            partition_table,
            pedigree_table,
            partition_description,
            pedigree_file,
            partition_hdfs_path,
            files
        )

        end = time()
        duration = end - start
        print(duration)

    def dataset_import(self, study_id, partition_config_file, pedigree_file,
                       pedigree_local_hdfs_path=None):
        db = self.storage_config.impala.db
        part_desc = ParquetPartitionDescription.from_config(
            partition_config_file)
        root_dir = os.path.dirname(partition_config_file)
        files_glob = part_desc.generate_file_access_glob()
        files_glob = os.path.join(root_dir, files_glob)
        files = glob.glob(files_glob)

        partition_path = self.storage_config.hdfs.base_dir
        partition_path = os.path.join(partition_path, study_id)
        for file in files:
            file_dir = os.path.dirname(file)
            file_dir = file_dir[file_dir.find('region_bin'):]
            file_dir = os.path.join(partition_path, file_dir)
            self._put_partition_file(file, file_dir)

        if not pedigree_local_hdfs_path:
            pedigree_hdfs_path = os.path.join(
                    partition_path, 'pedigree', 'pedigree.ped')
        else:
            pedigree_hdfs_path = os.path.join(
                partition_path, pedigree_local_hdfs_path)

        self.hdfs_helpers.put(pedigree_file, pedigree_hdfs_path)

        files = list(map(lambda f: f[f.find('region_bin'):], files))

        self.impala_load_dataset(
            study_id, part_desc, pedigree_hdfs_path, db, partition_path, files
        )


STUDY_CONFIG_TEMPLATE = '''
[genotypeDataStudy]
id = {id}
genotype_storage = {genotype_storage}


[tables]
pedigree = {pedigree_table}
variant = {variant_table}
'''
