import os
from box import Box

from dae.pheno.pheno_factory import PhenoFactory

from dae.studies.study import Study
from dae.studies.dataset import Dataset
from dae.studies.study_wrapper import StudyWrapper
from dae.studies.study_config_parser import StudyConfigParser
from dae.studies.dataset_config_parser import DatasetConfigParser

from dae.backends.vcf.raw_vcf import RawFamilyVariants
from dae.backends.configure import Configure

from dae.backends.impala.impala_helpers import ImpalaHelpers
from dae.backends.impala.impala_variants import ImpalaFamilyVariants


class VariantsDb(object):

    FILE_FORMATS = set(['vcf', 'impala'])

    def __init__(self, dae_config, pheno_factory=None):
        self.dae_config = dae_config

        if pheno_factory is None:
            pheno_factory = PhenoFactory(dae_config=dae_config)
        self.pheno_factory = pheno_factory

        self.study_configs = \
            StudyConfigParser.read_and_parse_directory_configurations(
                dae_config.studies_db.dir,
                dae_config.dae_data_dir,
                defaults={'conf': dae_config.default_configuration.conf_file}
            )

        self.dataset_configs = \
            DatasetConfigParser.read_and_parse_directory_configurations(
                dae_config.datasets_db.dir,
                dae_config.dae_data_dir,
                self.study_configs,
                defaults={'conf': dae_config.default_configuration.conf_file},
                fail_silently=True
            )

        self._study_cache = {}
        self._study_wrapper_cache = {}

        self._dataset_cache = {}
        self._dataset_wrapper_cache = {}

        self._configuration_check()

    def _configuration_check(self):
        studies_ids = set(self.get_studies_ids())
        dataset_ids = set(self.get_datasets_ids())

        overlapping = studies_ids.intersection(dataset_ids)

        assert overlapping == set(), \
            "Overlapping studies and datasets ids: {}".format(overlapping)

    def get_studies_ids(self):
        return list(self.study_configs.keys())

    def get_study_config(self, study_id):
        self.load_study_cache({study_id})
        if study_id not in self._study_cache:
            return None

        return self._study_cache.get(study_id).config

    def get_study(self, study_id):
        self.load_study_cache({study_id})
        if study_id not in self._study_cache:
            return None

        return self._study_cache[study_id]

    def get_study_wdae_wrapper(self, study_id):
        self.load_study_cache({study_id})

        if study_id not in self._study_wrapper_cache:
            return None

        return self._study_wrapper_cache[study_id]

    def get_all_studies(self):
        self.load_study_cache()

        return list(self._study_cache.values())

    def get_all_studies_wrapper(self):
        self.load_study_cache()

        return list(self._study_wrapper_cache.values())

    def get_all_study_configs(self):
        self.load_study_cache()

        return [study.config for study in self._study_cache.values()]

    def get_datasets_ids(self):
        return list(self.dataset_configs.keys())

    def get_dataset_config(self, dataset_id):
        self.load_dataset_cache({dataset_id})
        if dataset_id not in self._dataset_cache:
            return None

        return self._dataset_cache.get(dataset_id).config

    def get_dataset(self, dataset_id):
        self.load_dataset_cache({dataset_id})

        if dataset_id not in self._dataset_cache:
            return None

        return self._dataset_cache[dataset_id]

    def get_dataset_wdae_wrapper(self, dataset_id):
        self.load_dataset_cache({dataset_id})

        if dataset_id not in self._dataset_wrapper_cache:
            return None

        return self._dataset_wrapper_cache[dataset_id]

    def get_all_datasets(self):
        self.load_dataset_cache()

        return list(self._dataset_cache.values())

    def get_all_datasets_wrapper(self):
        self.load_dataset_cache()

        return list(self._dataset_wrapper_cache.values())

    def get_all_dataset_configs(self):
        self.load_dataset_cache()

        return [dataset.config for dataset in self._dataset_cache.values()]

    def get_all_ids(self):
        return self.get_studies_ids() + self.get_datasets_ids()

    def get_config(self, config_id):
        study_config = self.get_study_config(config_id)
        dataset_config = self.get_dataset_config(config_id)
        return study_config if study_config else dataset_config

    def get(self, object_id):
        study = self.get_study(object_id)
        dataset = self.get_dataset(object_id)
        return study if study else dataset

    def get_wdae_wrapper(self, wdae_wrapper_id):
        study_wdae_wrapper = self.get_study_wdae_wrapper(wdae_wrapper_id)
        dataset_wdae_wrapper = self.get_dataset_wdae_wrapper(wdae_wrapper_id)
        return study_wdae_wrapper\
            if study_wdae_wrapper else dataset_wdae_wrapper

    def get_all_configs(self):
        study_configs = self.get_all_study_configs()
        dataset_configs = self.get_all_dataset_configs()
        return study_configs + dataset_configs

    def get_all(self):
        studies = self.get_all_studies()
        datasets = self.get_all_datasets()
        return studies + datasets

    def get_all_wrappers(self):
        study_wrappers = self.get_all_studies_wrapper()
        dataset_wrappers = self.get_all_datasets_wrapper()
        return study_wrappers + dataset_wrappers

    def load_study_cache(self, study_ids=None):
        if study_ids is None:
            study_ids = set(self.get_studies_ids())

        assert isinstance(study_ids, set)

        cached_ids = set(self._study_cache.keys())
        if study_ids != cached_ids:
            to_load = study_ids - cached_ids
            for study_id in to_load:
                self._load_study_in_cache(study_id)

    def _load_study_in_cache(self, study_id):
        conf = self.study_configs.get(study_id)
        if not conf:
            return

        study = self.make_study(conf)
        if study is None:
            return
        self._study_cache[study_id] = study
        self._study_wrapper_cache[study_id] = \
            StudyWrapper(study, self.pheno_factory)

    def load_dataset_cache(self, dataset_ids=None):
        if dataset_ids is None:
            dataset_ids = set(self.get_datasets_ids())

        assert isinstance(dataset_ids, set)

        cached_ids = set(self._dataset_cache.keys())
        if dataset_ids != cached_ids:
            to_load = dataset_ids - cached_ids
            for dataset_id in to_load:
                self._load_dataset_in_cache(dataset_id)

    def _load_dataset_in_cache(self, dataset_id):
        conf = self.dataset_configs.get(dataset_id)
        if not conf:
            return

        dataset = self.make_dataset(conf)
        if dataset is None:
            return
        self._dataset_cache[dataset_id] = dataset
        self._dataset_wrapper_cache[dataset_id] = StudyWrapper(
            dataset, self.pheno_factory)

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

        if dataset_config is None:
            return None

        studies = []
        for study_id in dataset_config.studies:
            study = self.get_study(study_id)

            if not study:
                raise ValueError(
                    "Unknown study: {}, known studies: [{}]".format(
                        dataset_config.studies,
                        ",".join(self.get_all_study_ids())
                    ))
            studies.append(study)
        assert studies

        return Dataset(dataset_config, studies)
