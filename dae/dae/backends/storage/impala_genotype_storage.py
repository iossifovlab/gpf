import os

from dae.backends.storage.genotype_storage import GenotypeStorage

from dae.backends.configure import Configure

from dae.backends.impala.impala_helpers import ImpalaHelpers
from dae.backends.impala.impala_variants import ImpalaFamilyVariants


class ImpalaGenotypeStorage(GenotypeStorage):
    
    def __init__(self, storage_config):
        super(ImpalaGenotypeStorage, self).__init__(storage_config)

        self._impala_connection = self._make_impala_connection()

    def _create_impala_connection(self):
        connection = ImpalaHelpers.create_impala_connection(
            self.storage_config.impala.host,
            self.storage_config.impala.port
        )

        return connection

    def get_backend(self, study_config, genomes_db):
        impala_config = self._impala_configuration(study_config).impala
        
        variants = ImpalaFamilyVariants(
            impala_config, self._impala_connection,
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
