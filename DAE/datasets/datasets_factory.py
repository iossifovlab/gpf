'''
Created on Feb 27, 2017

@author: lubo
'''
import copy

from datasets.config import DatasetsConfig
from datasets.dataset import Dataset


class DatasetsFactory(dict):

    def __init__(self, datasets_config=None):
        if datasets_config is None:
            self.datasets_config = DatasetsConfig()
        else:
            self.datasets_config = datasets_config

    def get_dataset(self, dataset_id):
        if dataset_id in self:
            return self[dataset_id]
        dataset_descriptor = self.datasets_config.get_dataset_desc(dataset_id)
        if dataset_descriptor is None:
            return None
        dataset = Dataset(dataset_descriptor)
        dataset.load()

        self[dataset_id] = dataset
        return dataset

    def get_datasets(self):
        result = []
        dataset_descriptors = self.get_description_datasets()
        for dataset_descriptor in dataset_descriptors:
            result.append(self.get_dataset(dataset_descriptor['id']))

        return result

    def get_description_datasets(self):
        datasets_description = self.datasets_config.get_datasets()
        result = []
        for desc in datasets_description:
            dataset_id = desc['id']
            if dataset_id not in self:
                self.get_dataset(dataset_id)
            dataset_description = self[dataset_id].descriptor
            result.append(copy.deepcopy(dataset_description))
        return result

    def get_description_dataset(self, dataset_id):
        dataset = self.get(dataset_id, None)
        if dataset is None:
            dataset_descriptor = \
                self.datasets_config.get_dataset_desc(dataset_id)
            if dataset_descriptor is None:
                return None
            self.get_dataset(dataset_id)
        dataset_description = self[dataset_id].descriptor
        return copy.deepcopy(dataset_description)
