import os

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
        
        variants = ImpalaFamilyVariants(
            impala_config, self.impala_connection,
            genomes_db.get_gene_models()
        )

        return variants

    def _impala_configuration(self, study_config):
        data_path = self._get_data_path(study_config.id)

        if 'pedigree_file' in study_config:
            pedigree_file = study_config.pedigree_file
        else:
            pedigree_file = "{}_pedigree.parquet".format(study_config.id)
        if 'variant_files' in study_config:
            variant_files = study_config.variant_files
        else:
            variant_files = "{}_variant*.pedigree".format(study_config.id)

        conf = {
            'impala': {
                'files': {
                    'pedigree': os.path.join(data_path, pedigree_file),
                    'variant': os.path.join(data_path, variant_files),
                },
                'db': self.storage_config.impala.db,
                'tables': {
                    'pedigree': '{}_pedigree'.format(study_config.id),
                    'variant': '{}_variant'.format(study_config.id),
                }
            }
        }
        return Configure(conf)
