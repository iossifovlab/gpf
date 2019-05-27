import os

from studies.study import Study
from backends.thrift.raw_thrift import ThriftFamilyVariants
from backends.vcf.raw_vcf import RawFamilyVariants
from backends.configure import Configure


class StudyFactory(object):

    FILE_FORMATS = set(['vcf', 'thrift'])

    def __init__(self, thrift_connection=None):
        self.thrift_connection = thrift_connection

    def thrift_configuration(self, study_config):
        assert study_config.file_format == 'thrift'
        prefix = study_config.prefix

        pedigree_file = study_config.pedigree_file
        summary_files = study_config.summary_files
        family_files = study_config.family_files
        effect_gene_files = study_config.effect_gene_files
        member_files = study_config.member_files

        conf = {
            'parquet': {
                'summary_variant': os.path.join(prefix, summary_files),
                'family_variant': os.path.join(prefix, family_files),
                'member_variant': os.path.join(prefix, member_files),
                'effect_gene_variant': os.path.join(prefix, effect_gene_files),
                'pedigree': os.path.join(prefix, pedigree_file),
                'db': 'parquet',
            }
        }
        return Configure(conf)

    def make_study(self, study_config):
        if study_config.file_format not in self.FILE_FORMATS:
            raise ValueError(
                "Unknown study format: {}\nKnown ones: {}"
                .format(
                    study_config.file_format, self.FILE_FORMATS)
            )

        if study_config.file_format == 'thrift':
            if self.thrift_connection is None:
                self.thrift_connection = \
                    ThriftFamilyVariants.get_thrift_connection()
            config = self.thrift_configuration(study_config).parquet

            variants = ThriftFamilyVariants(
                config=config, thrift_connection=self.thrift_connection)
            return Study(study_config, variants)
        else:
            variants = RawFamilyVariants(
                prefix=study_config.prefix)

            return Study(study_config, variants)
