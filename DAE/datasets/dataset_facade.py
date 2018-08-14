from datasets.dataset import DatasetWrapper
from datasets.dataset_factory import DatasetFactory
from datasets.datasets_definition import DirectoryEnabledDatasetsDefinition
from studies.study_definition import SingleFileStudiesDefinition


class DatasetFacade(object):

    _dataset_cache = {}

    def __init__(self):
        study_definition = SingleFileStudiesDefinition()
        self.dataset_definition = DirectoryEnabledDatasetsDefinition()
        self.dataset_factory = DatasetFactory(
            _class=DatasetWrapper, studies_definition=study_definition)

    def get_dataset(self, dataset_id):
        self.load_cache({dataset_id})

        return self._dataset_cache[dataset_id]

    def get_all_datasets(self):
        self.load_cache()

        return list(self._dataset_cache.values())

    def get_all_dataset_ids(self):
        return [
            conf.dataset_id
            for conf in self.dataset_definition.get_all_dataset_configs()
        ]

    def get_all_dataset_configs(self):
        return self.dataset_definition.get_all_dataset_configs()

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
        conf = self.dataset_definition.get_dataset_config(dataset_id)
        if not conf:
            return

        self._dataset_cache[dataset_id] = \
            self.dataset_factory.get_dataset(conf)

