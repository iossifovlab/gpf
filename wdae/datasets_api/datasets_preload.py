'''
Created on Feb 17, 2017

@author: lubo
'''
from preloaded.register import Preload
from datasets.datasets_factory import DatasetsFactory
from datasets.config import DatasetsConfig


class DatasetsPreload(Preload):

    def __init__(self):
        super(DatasetsPreload, self).__init__()
        self.dataset_config = DatasetsConfig()
        self.factory = DatasetsFactory(self.dataset_config)

    def load(self):
        for ds in self.dataset_config.get_datasets():
            dataset_id = ds['id']
            self.factory.get_dataset(dataset_id)

    def get(self):
        return self

    def get_factory(self):
        return self.factory

    def get_config(self):
        return self.dataset_config
