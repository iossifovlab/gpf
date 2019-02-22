from studies.study_wrapper import StudyWrapper


class DatasetFacade(object):

    _dataset_cache = {}
    _dataset_wrapper_cache = {}

    def __init__(self, dataset_definitions, dataset_factory):

        self.dataset_definition = dataset_definitions
        self.dataset_factory = dataset_factory

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

    # def get_dataset_by_study_group(self, study_group_id):
    #     for dataset_config in self.get_all_dataset_configs():
    #         if dataset_config.study_group == study_group_id:
    #             return self.get_dataset(dataset_config.id)

    #     return None

    def get_all_datasets(self):
        self.load_cache()

        return list(self._dataset_cache.values())

    def get_all_datasets_wrapper(self):
        self.load_cache()

        return list(self._dataset_wrapper_cache.values())

    def get_all_dataset_ids(self):
        return [
            conf.id
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

        dataset = self.dataset_factory.make_dataset(conf)
        self._dataset_cache[dataset_id] = dataset
        self._dataset_wrapper_cache[dataset_id] = StudyWrapper(dataset)
            
