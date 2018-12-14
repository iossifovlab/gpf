from builtins import object

from datasets.dataset_facade import DatasetFacade
from datasets_api.models import Dataset


__all__ = ['get_datasets_manager']


class DatasetsManager(object):

    def __init__(self):
        self.facade = None
        self.dataset_definition = None
        self.dataset_factory = None

    def reload_dataset_facade(self):
        self.facade = DatasetFacade(
            dataset_definition=self.dataset_definition,
            dataset_factory=self.dataset_factory)

        for dataset_id in self.facade.get_all_dataset_ids():
            Dataset.recreate_dataset_perm(dataset_id, [])

    def get_dataset_facade(self):
        if self.facade is None:
            self.reload_dataset_facade()
            assert self.facade is not None

        return self.facade


datasets_manager = DatasetsManager()


def get_datasets_manager():
    return datasets_manager
