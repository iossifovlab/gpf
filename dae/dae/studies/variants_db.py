from dae.pheno.pheno_factory import PhenoFactory

from dae.studies.study_wrapper import StudyWrapper
from dae.studies.study_factory import StudyFactory
from dae.studies.study_config_parser import StudyConfigParser
from dae.studies.dataset_config_parser import DatasetConfigParser


class VariantsDb(object):

    def __init__(self, dae_config, pheno_factory=None):

        self.dae_config = dae_config

        self.study_factory = StudyFactory(dae_config, self)

        if pheno_factory is None:
            pheno_factory = PhenoFactory(dae_config=dae_config)
        self.pheno_factory = pheno_factory

        study_configs = \
            StudyConfigParser.read_and_parse_directory_configurations(
                dae_config.studies_db.dir,
                dae_config.dae_data_dir,
                defaults={'conf': dae_config.default_configuration.conf_file}
            )
        self.study_configs = {sc.id: sc for sc in study_configs}

        dataset_configs = \
            DatasetConfigParser.read_directory_configurations(
                dae_config.datasets_db.dir,
                dae_config.dae_data_dir,
                defaults={'conf': dae_config.default_configuration.conf_file},
                fail_silently=True
            )
        self.dataset_configs = {
            dc[DatasetConfigParser.SECTION].id: dc for dc in dataset_configs
        }

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

        study = self.study_factory.make_study(conf)
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

        dataset = self.study_factory.make_dataset(conf)
        if dataset is None:
            return
        self._dataset_cache[dataset_id] = dataset
        self._dataset_wrapper_cache[dataset_id] = StudyWrapper(
            dataset, self.pheno_factory)
