import os

from studies.study import Study
from backends.vcf.raw_vcf import RawFamilyVariants
from backends.configure import Configure

from backends.impala.impala_backend import ImpalaBackend
from backends.impala.impala_variants import ImpalaFamilyVariants


class StudyFactory(object):

    FILE_FORMATS = set(['vcf', 'impala'])

    def __init__(self, dae_config, thrift_connection=None):
        self.thrift_connection = thrift_connection
        self.dae_config = dae_config

    def impala_configuration(self, study_config):
        assert study_config.file_format == 'impala'
        prefix = study_config.prefix
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
                    'pedigree': os.path.join(prefix, pedigree_file),
                    'variant': os.path.join(prefix, variant_files),
                },
                'db': self.dae_config.impala_db,
                'tables': {
                    'pedigree': '{}_pedigree'.format(study_config.id),
                    'variant': '{}_variant'.format(study_config.id),
                }
            }
        }
        return Configure(conf)

    def make_impala_backend(self):

        backend = ImpalaBackend(
            self.dae_config.impala_host, self.dae_config.impala_port,
            self.dae_config.hdfs_host, self.dae_config.hdfs_port)

        return backend

    def make_study(self, study_config):
        if study_config.file_format not in self.FILE_FORMATS:
            raise ValueError(
                "Unknown study format: {}\nKnown ones: {}"
                .format(
                    study_config.file_format, self.FILE_FORMATS)
            )

        if study_config.file_format == 'impala':
            impala_config = self.impala_configuration(study_config).impala
            impala_backend = self.make_impala_backend()
            variants = ImpalaFamilyVariants(impala_config, impala_backend)
            return Study(study_config, variants)
        else:
            variants = RawFamilyVariants(
                prefix=study_config.prefix)

            return Study(study_config, variants)
