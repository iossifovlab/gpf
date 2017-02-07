'''
Created on Feb 6, 2017

@author: lubo
'''
from common.query_base import QueryBase
from DAE import vDB
import itertools


class PedigreeLegend(dict):

    def __init__(self, pedigree_selector):
        self.id = pedigree_selector['id']
        self.name = pedigree_selector['name']
        self.domain = pedigree_selector['domain']
        self.values = dict([(v['id'], v) for v in self.domain])
        self.default = pedigree_selector['default']
        self['id'] = self.id
        self['values'] = self.values
        self['domain'] = self.domain
        self['name'] = self.name

    def get_color(self, value_id):
        value = self.values.get(value_id, None)
        if value is None:
            return self.default['color']
        else:
            return value['color']


class QueryDataset(QueryBase):

    @staticmethod
    def idlist_get(named_list, name):
        for el in named_list:
            if name == el['id']:
                return el
        return None

    def __init__(self, datasets):
        self.datasets = {}
        for dataset in datasets:
            self.datasets[dataset['id']] = dataset

    def get_variants(self, datasetId, safe=True, **kwargs):
        dataset = self.get_dataset(datasetId=datasetId, safe=safe, **kwargs)
        denovo = self.get_denovo_variants(dataset, safe, **kwargs)

        return itertools.chain.from_iterable([denovo])

    def get_denovo_variants(self, dataset, safe=True, **kwargs):
        denovo_studies = self.get_denovo_studies(dataset)
        denovo_filters = self.get_denovo_filters(dataset, safe, **kwargs)

        seen_vs = set()
        for st in denovo_studies:
            for v in st.get_denovo_variants(**denovo_filters):
                v_key = v.familyId + v.location + v.variant
                if v_key in seen_vs:
                    continue
                yield v
                seen_vs.add(v_key)

    def get_pedigree_selector(self, dataset, **kwargs):
        pedigrees = dataset['pedigreeSelectors']
        pedigree = pedigrees[0]
        if 'pedigreeSelector' in kwargs:
            pedigree = self.idlist_get(pedigrees, kwargs['pedigreeSelector'])
        assert pedigree is not None
        return pedigree

    def get_dataset(self, **kwargs):
        assert 'datasetId' in kwargs
        dataset_id = kwargs['datasetId']

        assert dataset_id in self.datasets
        dataset = self.datasets[dataset_id]
        assert dataset is not None

        return dataset

    def get_legend(self, dataset, **kwargs):
        pedigree = self.get_pedigree_selector(dataset, **kwargs)
        return PedigreeLegend(pedigree)

    def get_effect_types(self, safe=True, **kwargs):
        assert 'effectTypes' in kwargs

        effect_types = kwargs['effectTypes']

        return self.build_effect_types(effect_types, safe)

    def get_studies(self, dataset):
        study_names = [st.strip() for st in dataset['studies'].split(',')]
        studies = [vDB.get_studies(st) for st in study_names]
        return [st for st in itertools.chain.from_iterable(studies)]

    def get_denovo_studies(self, dataset, **kwargs):
        return [st for st in self.get_studies(dataset) if st.has_denovo]

    def get_transmitted_studies(self, dataset, **kwargs):
        return [st for st in self.get_studies(dataset) if st.has_transmitted]

    def get_denovo_filters(self, dataset, safe=True, **kwargs):
        return {
            'effectTypes': self.get_effect_types(
                safe=safe, dataset=dataset, **kwargs)
        }
