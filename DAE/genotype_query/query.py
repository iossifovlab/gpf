'''
Created on Feb 6, 2017

@author: lubo
'''
from common.query_base import QueryBase


class QueryDataset(QueryBase):

    @staticmethod
    def get_named(named_list, name):
        for el in named_list:
            if name == el['id']:
                return el
        return None

    def __init__(self, datasets):
        self.datasets = {}
        for dataset in datasets:
            self.datasets[dataset['id']] = dataset

    def get_variants(self, dataset_id, **kwargs):
        assert dataset_id is not None
        assert dataset_id in self.datasets

    def get_pedigree_selector(self, dataset, **kwargs):
        pedigrees = dataset['pedigreeSelectors']
        pedigree = pedigrees[0]
        if 'pedigree_selector' in kwargs:
            pedigree = self.get_named(pedigrees, kwargs['pedigree_selector'])
        assert pedigree is not None
        return pedigree

    def get_dataset(self, dataset_id):
        assert dataset_id is not None
        assert dataset_id in self.datasets
        dataset = self.datasets[dataset_id]
        assert dataset is not None

        return dataset

    def get_legend(self, dataset_id, **kwargs):
        dataset = self.get_dataset(dataset_id)
        pedigree = self.get_pedigree_selector(dataset, **kwargs)

        values = pedigree['domain'][:]
        default_value = pedigree['default']
        if self.get_named(values, default_value['id']) is None:
            values.append(default_value)

        return {
            'name': pedigree['name'],
            'values': values
        }
