from studies.study_wrapper import StudyWrapper
from studies.dataset_config_parser import DatasetConfigParser


class DatasetFacade(object):

    def __init__(self, dataset_configs, dataset_factory, pheno_factory):
        self._dataset_cache = {}
        self._dataset_wrapper_cache = {}

        self.dataset_configs = {
            dc[DatasetConfigParser.SECTION].id: dc for dc in dataset_configs
        }

        self.dataset_factory = dataset_factory
        self.pheno_factory = pheno_factory

    def get_dataset(self, dataset_id):
        self.load_cache({dataset_id})

        if dataset_id not in self._dataset_cache:
            return None

        return self._dataset_cache[dataset_id]

    def get_dataset_wdae_wrapper(self, dataset_id):
        self.load_cache({dataset_id})

        if dataset_id not in self._dataset_wrapper_cache:
            return None

        return self._dataset_wrapper_cache[dataset_id]

    def get_all_datasets(self):
        self.load_cache()

        return list(self._dataset_cache.values())

    def get_all_datasets_wrapper(self):
        self.load_cache()

        return list(self._dataset_wrapper_cache.values())

    def get_all_dataset_ids(self):
        return list(self.dataset_configs.keys())

    def get_all_dataset_configs(self):
        self.load_cache()

        return [dataset.config for dataset in self._dataset_cache.values()]

    def get_dataset_config(self, dataset_id):
        self.load_cache({dataset_id})
        if dataset_id not in self._dataset_cache:
            return None

        return self._dataset_cache.get(dataset_id).config

    def load_cache(self, dataset_ids=None):
        if dataset_ids is None:
            dataset_ids = set(self.get_all_dataset_ids())

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

        dataset = self.dataset_factory.make_dataset(conf)
        if dataset is None:
            return
        self._dataset_cache[dataset_id] = dataset
        self._dataset_wrapper_cache[dataset_id] = StudyWrapper(
            dataset, self.pheno_factory)
