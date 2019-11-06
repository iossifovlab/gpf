import os
from box import Box

from dae.backends.storage.genotype_storage import GenotypeStorage

from dae.backends.impala.hdfs_helpers import HdfsHelpers
from dae.backends.impala.impala_helpers import ImpalaHelpers
from dae.backends.impala.impala_variants import ImpalaFamilyVariants


class ImpalaGenotypeStorage(GenotypeStorage):
    
    def __init__(self, storage_config):
        super(ImpalaGenotypeStorage, self).__init__(storage_config)

        self._impala_connection = None
        self._impala_helpers = None
        self._hdfs_helpers = None

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

    def get_backend(self, study_id, genomes_db):
        impala_config = self._impala_storage_config(study_id)
        
        variants = ImpalaFamilyVariants(
            impala_config, self.impala_connection,
            genomes_db.get_gene_models()
        )

        return variants

    def _impala_config(self, study_id, pedigree_path, variants_path):
        study_impala_config = self._impala_storage_config(study_id)
        import_files_config = self._hdfs_parquet_files_config(
            study_id, pedigree_path, variants_path
        )

        return Box({**study_impala_config, **import_files_config})

    def _impala_storage_config(self, study_id):
        conf = {
                'db': self.storage_config.impala.db,
                'tables': {
                'pedigree': '{}_pedigree'.format(study_id),
                'variant': '{}_variant'.format(study_id),
            }
                }

        return Box(conf)

    def _hdfs_parquet_files_config(
            self, study_id, pedigree_path, variants_path):
        pedigree_dirname = self.get_hdfs_dir(study_id, 'pedigree')
        variants_dirname = self.get_hdfs_dir(study_id, 'variants')

        self.hdfs_helpers.put_content(pedigree_path, pedigree_dirname)
        self.hdfs_helpers.put_content(variants_path, variants_dirname)

        pedigree_files = self.hdfs_helpers.list_dir(pedigree_dirname)
        variants_files = self.hdfs_helpers.list_dir(variants_dirname)

        conf = {
            'files': {
                'pedigree': pedigree_files,
                'variants': variants_files
            }
        }
        return Box(conf)
