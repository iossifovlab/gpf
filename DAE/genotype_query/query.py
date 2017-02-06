'''
Created on Feb 6, 2017

@author: lubo
'''
from common.query_base import QueryBase


class QueryDataset(QueryBase):

    def __init__(self, datasets):
        self.datasets = {}
        for dataset in datasets:
            self.datasets[dataset['id']] = dataset

    def get_variants(self, dataset_id, **kwargs):
        assert dataset_id is not None
        assert dataset_id in self.datasets
