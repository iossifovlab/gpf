'''
Created on Feb 27, 2017

@author: lubo
'''
import copy

from datasets.config import DatasetsConfig
from datasets.dataset import Dataset
from datasets.metadataset import MetaDataset
import logging


logger = logging.getLogger(__name__)


class DatasetsFactory(dict):

    def __init__(self, datasets_config=None):
        if datasets_config is None:
            self.datasets_config = DatasetsConfig()
        else:
            self.datasets_config = datasets_config

    def __load_single_dataset(self, dataset_id):
        dataset_descriptor = self.datasets_config.get_dataset_desc(dataset_id)
        if dataset_descriptor is None:
            return None
        if dataset_id != MetaDataset.ID:
            dataset = Dataset(dataset_descriptor)
        else:
            all_dataset_ids = self.datasets_config.get_dataset_ids()
            all_dataset_ids.remove(MetaDataset.ID)
            dataset = MetaDataset(
                self.datasets_config.get_dataset_desc(MetaDataset.ID),
                [self.get_dataset(dataset_id)
                 for dataset_id in all_dataset_ids])
        dataset.load()
        return dataset

    def get_dataset(self, dataset_id):
        if dataset_id in self:
            return self[dataset_id]
        else:
            logger.warn("dataset {} NOT FOUND in dataset cache".format(
                dataset_id))
            dataset = self.__load_single_dataset(dataset_id)
            if dataset is not None:
                self[dataset_id] = dataset
            return dataset

    def get_datasets(self):
        result = []
        dataset_descriptors = self.get_description_datasets()
        for dataset_descriptor in dataset_descriptors:
            result.append(self.get_dataset(dataset_descriptor['id']))

        return result

    def get_dataset_by_name(self, name):
        for desc in self.datasets_config.get_datasets():
            if desc['name'] == name:
                return self.get_dataset(desc['id'])
        return None

    def get_description_datasets(self):
        datasets_ids = self.datasets_config.get_dataset_ids()
        datasets_ids.remove(MetaDataset.ID)
        datasets_description = [self.datasets_config.get_dataset_desc(dataset_id)
                for dataset_id in datasets_ids]

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
