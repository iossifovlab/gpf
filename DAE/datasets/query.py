'''
Created on Feb 6, 2017

@author: lubo
'''
from common.query_base import QueryBase
import itertools


class QueryDataset(QueryBase):

    def __init__(self):
        pass

    def get_variants(self, dataset_descriptor, safe=True, **kwargs):
        denovo = self.get_denovo_variants(dataset_descriptor, safe, **kwargs)
        return itertools.chain.from_iterable([denovo])

#     def get_dataset(self, **kwargs):
#         assert 'datasetId' in kwargs
#         dataset_id = kwargs['datasetId']
#
#         assert dataset_id in self.datasets
#         dataset = self.datasets[dataset_id]
#         assert dataset is not None
#
#         return dataset
