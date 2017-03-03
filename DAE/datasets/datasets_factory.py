'''
Created on Feb 27, 2017

@author: lubo
'''
from datasets.config import DatasetsConfig
from datasets.dataset import Dataset
from datasets.ssc_dataset import SSCDataset


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
        if dataset_id == 'SSC':
            dataset = SSCDataset(dataset_descriptor)
        else:
            dataset = Dataset(dataset_descriptor)
        dataset.load()

        self[dataset_id] = dataset
        return dataset
