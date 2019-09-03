import os
from box import Box

from dae.studies.study import Study
from dae.studies.dataset import Dataset
from dae.studies.dataset_config_parser import DatasetConfigParser

from dae.backends.vcf.raw_vcf import RawFamilyVariants
from dae.backends.configure import Configure

from dae.backends.impala.impala_helpers import ImpalaHelpers
from dae.backends.impala.impala_variants import ImpalaFamilyVariants


class StudyFactory(object):

    FILE_FORMATS = set(['vcf', 'impala'])

    def __init__(self, dae_config, variants_db):
        self.dae_config = dae_config
        self.variants_db = variants_db

    def _impala_configuration(self, study_config):
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
                'db': self.dae_config.impala.db,
                'tables': {
                    'pedigree': '{}_pedigree'.format(study_config.id),
                    'variant': '{}_variant'.format(study_config.id),
                }
            }
        }
        return Configure(conf)

    def _make_impala_connection(self):
        connection = ImpalaHelpers.get_impala(
            self.dae_config.impala.host, self.dae_config.impala.port)

        return connection

    def _get_studies_configs(self, dataset_config):
        studies_configs = []
        for study_id in DatasetConfigParser._split_str_option_list(
                dataset_config[DatasetConfigParser.SECTION].studies):
            study_config = self.variants_db.get_study_config(study_id)
            if study_config:
                studies_configs.append(study_config)
        return studies_configs

    def make_study(self, study_config):
        if study_config is None:
            return None

        if study_config.file_format not in self.FILE_FORMATS:
            raise ValueError(
                "Unknown study format: {}\nKnown ones: {}"
                .format(
                    study_config.file_format, self.FILE_FORMATS)
            )

        if study_config.file_format == 'impala':
            impala_config = self._impala_configuration(study_config).impala
            impala_connection = self._make_impala_connection()
            variants = ImpalaFamilyVariants(impala_config, impala_connection)
            return Study(study_config, variants)
        else:
            variants = RawFamilyVariants(prefix=study_config.prefix)

            return Study(study_config, variants)

    def make_dataset(self, dataset_config):
        assert isinstance(dataset_config, Box), type(dataset_config)

        study_configs = self._get_studies_configs(dataset_config)
        dataset_config = \
            DatasetConfigParser.parse(dataset_config, study_configs)
        if dataset_config is None:
            return None

        studies = []
        for study_id in dataset_config.studies:
            study = self.variants_db.get_study(study_id)

            if not study:
                raise ValueError(
                    "Unknown study: {}, known studies: [{}]".format(
                        dataset_config.studies,
                        ",".join(self.variants_db.get_all_study_ids())
                    ))
            studies.append(study)
        assert studies

        return Dataset(dataset_config, studies)
