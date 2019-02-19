'''
Created on Feb 16, 2017

@author: lubo
'''
from __future__ import print_function

import os
import traceback
import sqlite3
from itertools import chain, product
from collections import OrderedDict
import cPickle
import logging

# from denovo_gene_sets import build_denovo_gene_sets
from gene.config import GeneInfoConfig
from datasets.config import DatasetsConfig
from datasets.metadataset import MetaDataset
from GeneTerms import loadGeneTerm
# from DAE import vDB
import DAE

LOGGER = logging.getLogger(__name__)


class GeneSetsCollection(GeneInfoConfig):

    def __init__(self, gene_sets_collection_id):
        super(GeneSetsCollection, self).__init__()

        assert gene_sets_collection_id != 'denovo'
        self.gsc_id = gene_sets_collection_id
        self.gene_sets_descriptions = None
        self.gene_sets_collections = None

    def _load(self):
        try:
            gene_sets_collection = self.gene_info.getGeneTerms(self.gsc_id)
        except Exception:
            traceback.print_exc()
            gene_sets_collection = loadGeneTerm(self.gsc_id)

        if gene_sets_collection.geneNS == 'id':
            def rF(x):
                if x in self.gene_info.genes:
                    return self.gene_info.genes[x].sym
            gene_sets_collection.renameGenes("sym", rF)

        if gene_sets_collection.geneNS != 'sym':
            raise Exception('Only work with id or sym namespace')
        return gene_sets_collection

    def load(self):
        if self.gene_sets_collections:
            return self.gene_sets_collections

        self.gene_sets_collections = self._load()

        self.gene_sets_descriptions = [
            {
                'name': key,
                'desc': value,
                'count': len(self.gene_sets_collections.t2G[key].keys())
            }
            for key, value in self.gene_sets_collections.tDesc.items()
        ]
        return self.gene_sets_collections

    def get_gene_sets(self, gene_sets_types=[], **kwargs):
        assert self.gene_sets_collections is not None
        assert self.gene_sets_descriptions is not None
        return self.gene_sets_descriptions

    def get_gene_sets_types_legend(self, **kwargs):
        return []

    def get_gene_set(self, gene_set_id, gene_sets_types=[], **kwargs):
        assert self.gene_sets_collections is not None

        if gene_set_id not in self.gene_sets_collections.t2G:
            return None
        syms = set(self.gene_sets_collections.t2G[gene_set_id].keys())
        count = len(syms)
        desc = self.gene_sets_collections.tDesc[gene_set_id]

        return {
            "name": gene_set_id,
            "count": count,
            "syms": syms,
            "desc": desc,
        }


class DenovoGeneSetsCollection(GeneInfoConfig):

    def __init__(self, gsc_id='denovo'):
        super(DenovoGeneSetsCollection, self).__init__()
        self.gsc_id = gsc_id
        self.datasets_config = DatasetsConfig()
        self._init_config()
        self.cache = {}

    def _init_config(self):
        self.datasets_pedigree_selectors = OrderedDict()
        for pedigree_selector_str in self._get_att_list(
                'datasets.pedigreeSelectors'):
            pedigree_selector = pedigree_selector_str.split(':')
            self.datasets_pedigree_selectors[pedigree_selector[0]] = {
                'id': pedigree_selector[1],
                'source': pedigree_selector[2]
            }

        self.standard_criterias = []
        for standard_criteria_id in self._get_att_list('standardCriterias'):
            segments_arrs = map(
                lambda segment_str: segment_str.split(':'),
                self._get_att_list(
                    'standardCriterias.{}.segments'.format(
                        standard_criteria_id)))
            self.standard_criterias.append(
                [{
                    'property': standard_criteria_id,
                    'name': segment_arr[0],
                    'value': segment_arr[1].split('.') if '.' in segment_arr[1] else segment_arr[1] 
                }
                    for segment_arr in segments_arrs]
            )

        self.recurrency_criterias = {}
        for recurrency_criteria_str in self._get_att_list(
                'recurrencyCriteria.segments'):
            name, from_count, to_count = \
                recurrency_criteria_str.strip().split(':')
            self.recurrency_criterias[name] = {
                'from': int(from_count),
                'to': int(to_count)
            }

        self.gene_sets_names = self._get_att_list('geneSetsNames')

    def _get_att_list(self, att_name):
        return self.gene_info.getGeneTermAttList(self.gsc_id, att_name)

    def _get_att(self, att_name):
        return self.gene_info.getGeneTermAtt(self.gsc_id, att_name)

    def load(self):
        if len(self.cache) == 0:
            self._pickle_cache()
        return self.get_gene_sets()

    def _pickle_cache(self):
        cache_file_path = self.gene_info.getGeneTermAtt(self.gsc_id, 'file')
        if os.path.exists(cache_file_path):
            infile = open(cache_file_path, 'r')
            self.cache = cPickle.load(infile)
        else:
            self._generate_cache()
            infile = open(cache_file_path, 'w')
            cPickle.dump(self.cache, infile)

    def build_cache(self, datasets=None):
        self._generate_cache(datasets)

    def _generate_cache(self, datasets=None):
        for dataset in self._get_dataset_descs(datasets):
            self._gene_sets_for(dataset)

    def _get_dataset_descs(self, datasets=None):
        if datasets is None:
            datasets = self.datasets_pedigree_selectors.keys()
        return [self.datasets_config.get_dataset_desc(gid)
                for gid in datasets]

    def get_gene_sets_types_legend(self, **kwargs):
        permitted_datasets = kwargs.get('permitted_datasets')
        return [
            {
                'datasetId': dataset_desc['id'],
                'datasetName': dataset_desc['name'],
                'phenotypes': self._get_configured_dataset_legend(dataset_desc)
            }
            for dataset_desc in self._get_dataset_descs()
            if permitted_datasets is None or
            dataset_desc['id'] in permitted_datasets
        ]

    def get_dataset_phenotypes(self, dataset_id):
        legend = self.get_gene_sets_types_legend(permitted_datasets=None)
        res = {
            r['datasetId']: r for r in legend
        }
        return [p['id'] for p in res[dataset_id]['phenotypes']]

    def _get_configured_dataset_legend(self, dataset_desc):
        configured_pedigree_selector_id = self.datasets_pedigree_selectors[
            dataset_desc['id']]['id']
        for pedigree_selector in dataset_desc['pedigreeSelectors']:
            if pedigree_selector['id'] == configured_pedigree_selector_id:
                return pedigree_selector.domain
        return None

    @staticmethod
    def _filter_gene_sets_types(gene_sets_types, permitted_datasets):
        return {k: v
                for k, v in gene_sets_types.items()
                if v and (permitted_datasets is None or
                          k in permitted_datasets)}

    @staticmethod
    def _format_description(
            gene_sets_types, include_datasets_desc=False,
            full_description=True):
        if full_description:
            return ";".join(["{}:{}".format(d, ",".join(p))
                             for d, p in gene_sets_types.items()])

        pedigree_selectors = ', '.join(set(chain(*gene_sets_types.values())))
        if include_datasets_desc:
            return '{}::{}'.format(
                ', '.join(set(gene_sets_types.keys())),
                pedigree_selectors)
        else:
            return pedigree_selectors

    def get_gene_sets(self, gene_sets_types={'SD': ['autism']}, **kwargs):
        gene_sets_types = self._filter_gene_sets_types(
            gene_sets_types,
            kwargs.get('permitted_datasets'))
        gene_sets_types_desc = self._format_description(
            gene_sets_types,
            kwargs.get('include_datasets_desc', True))
        result = []
        for gsn in self.gene_sets_names:
            gene_set_syms = self._get_gene_set_syms(gsn, gene_sets_types)
            if gene_set_syms:
                result.append({
                    'name': gsn,
                    'count': len(gene_set_syms),
                    'syms': gene_set_syms,
                    'desc': '{} ({})'.format(gsn, gene_sets_types_desc)
                })
        return result

    def get_gene_set(self, gene_set_id, gene_sets_types={'SD': ['autism']},
                     **kwargs):
        gene_sets_types = self._filter_gene_sets_types(
            gene_sets_types,
            kwargs.get('permitted_datasets'))
        syms = self._get_gene_set_syms(gene_set_id, gene_sets_types)
        if not syms:
            return None

        return {
            "name": gene_set_id,
            "count": len(syms),
            "syms": syms,
            "desc": "{} ({})".format(
                gene_set_id,
                self._format_description(
                    gene_sets_types,
                    kwargs.get('include_datasets_desc', False),
                    kwargs.get('full_dataset_desc', True)))
        }

    def gene_set(self, gene_set_id, gene_sets_types={'SD': ['autims']}):
        gs = self.get_gene_set(gene_set_id, gene_sets_types)
        return gs['syms']

    def get_denovo_sets(self, gene_sets_types={'SD': ['autims']}):
        for k, v in gene_sets_types.items():
            if not v:
                v = self.get_dataset_phenotypes(k)
                gene_sets_types[k] = v

        gss = self.get_gene_sets(gene_sets_types)
        return {g['name']: g['syms'] for g in gss}

    def _get_gene_set_syms(self, gene_set_id, gene_sets_types):
        criterias = set(gene_set_id.split('.'))
        recurrency_criterias = criterias & set(
            self.recurrency_criterias.keys())
        standard_criterias = criterias - recurrency_criterias
        if len(recurrency_criterias) > 0:
            recurrency_criteria = self.recurrency_criterias[next(
                iter(recurrency_criterias))]
        else:
            recurrency_criteria = None

        genes_families = {}
        for dataset_id, pedigree_selector_values in gene_sets_types.items():
            for pedigree_selector_value in pedigree_selector_values:
                ds_pedigree_genes_families = self._get_gene_families(
                    self.cache,
                    {dataset_id, pedigree_selector_value} | standard_criterias)
                for gene, families in ds_pedigree_genes_families.items():
                    genes_families.setdefault(gene, set()).update(families)

        if recurrency_criteria:
            if recurrency_criteria['to'] < 0:
                def filter_lambda(item): return len(
                    item[1]) >= recurrency_criteria['from']
            else:
                def filter_lambda(item):
                    return len(item[1]) >= recurrency_criteria['from'] \
                        and len(item[1]) < recurrency_criteria['to']

            matching_genes = map(lambda item: item[0],
                                 filter(filter_lambda, genes_families.items()))
        else:
            matching_genes = genes_families.keys()
        return set(matching_genes)

    @classmethod
    def _get_gene_families(cls, cache, criterias):
        if len(cache) == 0:
            return {}
        cache_keys = cache.keys()
        next_keys = criterias.intersection(cache_keys)
        if len(next_keys) == 0:
            result = {}
            if type(cache[cache_keys[0]]) != set:
                # still not the end of the tree
                for key in cache_keys:
                    for gene, families in cls._get_gene_families(
                            cache[key],
                            criterias).items():
                        result.setdefault(gene, set()).update(families)
            elif len(criterias) == 0:
                # end of tree with satisfied criterias
                result.update(cache)
            return result
        next_key = next_keys.pop()
        # next_criterias = criterias - {next_key}
        return cls._get_gene_families(cache[next_key], criterias - {next_key})

    def _gene_sets_for(self, dataset):
        assert dataset['id'] in self.datasets_pedigree_selectors, \
            [dataset['id'], self.datasets_pedigree_selectors]

        pedigree_selector = self.datasets_pedigree_selectors[
            dataset['id']]['source']
        pedigree_selector_values = map(
            lambda value: value['id'],
            self._get_configured_dataset_legend(dataset))

        dataset_cache = {value: {} for value in pedigree_selector_values}
        self.cache[dataset['id']] = dataset_cache

        for criterias_combination in product(*self.standard_criterias):
            search_args = {criteria['property']: criteria['value']
                           for criteria in criterias_combination}
            variants = list(DAE.vDB.get_denovo_variants(dataset['studies'],
                                                        **search_args))
            for pedigree_selector_value in pedigree_selector_values:
                cache = self._init_criterias_cache(
                    dataset_cache[pedigree_selector_value],
                    criterias_combination)
                self._add_genes_families(cache, pedigree_selector,
                                         pedigree_selector_value, variants)

    @staticmethod
    def _init_criterias_cache(dataset_cache, criterias_combination):
        cache = dataset_cache
        for criteria in criterias_combination:
            cache = cache.setdefault(criteria['name'], {})
        return cache

    @classmethod
    def _add_genes_families(cls, cache, pedigree_selector,
                            pedigree_selector_value, variants):
        for variant in cls._filter_by_pedigree_selector(
                pedigree_selector, pedigree_selector_value,
                variants):
            gene_symbols = {ge['sym']
                            for ge in variant.requestedGeneEffects}
            family_id = variant.familyId
            for gene in gene_symbols:
                cache.setdefault(gene, set()).add(family_id)

    @staticmethod
    def _filter_by_pedigree_selector(pedigree_selector, value, variants):
        if value == 'unaffected':
            for v in variants:
                if pedigree_selector in v.family_atts and 'sib' in v.inChS:
                    yield v
        else:
            for v in variants:
                if pedigree_selector in v.family_atts and \
                        v.family_atts[pedigree_selector] == value and \
                        'prb' in v.inChS:
                    yield v


class MetaDenovoGeneSetsCollection(DenovoGeneSetsCollection):

    def __init__(self):
        super(MetaDenovoGeneSetsCollection, self).__init__('metadenovo')

    def _generate_cache(self):
        raise Exception('MetaDenovoGeneSetsCollections expects to have already'
                        ' generated cache file')

    def get_gene_sets(self, gene_sets_types={MetaDataset.ID: ['autism']},
                      **kwargs):
        permitted_datasets = kwargs.get('permitted_datasets', [MetaDataset.ID])
        permitted_datasets.remove(MetaDataset.ID)
        denovo_gene_sets_types = {datasetId: gene_sets_types[MetaDataset.ID]
                                  for datasetId in permitted_datasets}

        return super(MetaDenovoGeneSetsCollection, self).get_gene_sets(
            denovo_gene_sets_types, permitted_datasets=permitted_datasets,
            include_datasets_desc=False)

    def get_gene_set(self, gene_set_id,
                     gene_sets_types={MetaDataset.ID: ['autism']}, **kwargs):
        permitted_datasets = kwargs.get('permitted_datasets', [MetaDataset.ID])
        permitted_datasets.remove(MetaDataset.ID)
        denovo_gene_sets_types = {datasetId: gene_sets_types[MetaDataset.ID]
                                  for datasetId in permitted_datasets}
        return super(MetaDenovoGeneSetsCollection, self).get_gene_set(
            gene_set_id, denovo_gene_sets_types,
            permitted_datasets=permitted_datasets,
            include_datasets_desc=False)

    def get_denovo_sets(self, phenotypes=['autism']):
        if phenotypes is None:
            phenotypes = self.get_dataset_phenotypes(MetaDataset.ID)
        gene_sets_types = {MetaDataset.ID: phenotypes}
        gss = self.get_gene_sets(
            gene_sets_types,
            permitted_datasets=self.datasets_config.get_dataset_ids())
        return {g['name']: g['syms'] for g in gss}

    def get_dataset_phenotypes(self):
        return super(MetaDenovoGeneSetsCollection, self).\
            get_dataset_phenotypes(MetaDataset.ID)


class GeneSetsCollections(GeneInfoConfig):

    def __init__(self):
        super(GeneSetsCollections, self).__init__()

        self.cache = self.config.get("cache", "file")
        self.db = None
        self.gene_sets_collections = {}
        self.gene_sets_collections_desc = None

    def connect(self):
        if self.db is not None:
            return self.db
        self.db = sqlite3.connect(self.cache, isolation_level="DEFERRED")
        return self.db

    def is_connected(self):
        return self.db is not None

    def get_gene_sets_collections(self, permitted_datasets=None):
        gene_sets_collections_desc = []
        for gsc_id in self.gene_info.getGeneTermIds():
            label = self.gene_info.getGeneTermAtt(gsc_id, "webLabel")
            formatStr = self.gene_info.getGeneTermAtt(gsc_id, "webFormatStr")
            if not label or not formatStr:
                continue
            gene_sets_types = self.get_gene_sets_collection(gsc_id)\
                .get_gene_sets_types_legend(
                    permitted_datasets=permitted_datasets)
            gene_sets_collections_desc.append(
                {
                    'desc': label,
                    'name': gsc_id,
                    'format': formatStr.split("|"),
                    'types': gene_sets_types,
                }
            )

        return gene_sets_collections_desc

    def has_gene_sets_collection(self, gsc_id):
        return any([
            gsc['name'] == gsc_id
            for gsc in self.get_gene_sets_collections()
        ])

    def get_gene_sets_collection(self, gene_sets_collection_id):
        if gene_sets_collection_id not in self.gene_sets_collections:
            if gene_sets_collection_id == 'denovo':
                gsc = DenovoGeneSetsCollection()
            elif gene_sets_collection_id == 'metadenovo':
                gsc = MetaDenovoGeneSetsCollection()
            else:
                gsc = GeneSetsCollection(gene_sets_collection_id)
            gsc.load()
            self.gene_sets_collections[gene_sets_collection_id] = gsc

        return self.gene_sets_collections.get(gene_sets_collection_id, None)

    def get_gene_sets(self, gene_sets_collection_id, gene_sets_types=[],
                      permitted_datasets=None):
        gsc = self.get_gene_sets_collection(gene_sets_collection_id)
        if gsc is None:
            return None

        return gsc.get_gene_sets(gene_sets_types,
                                 permitted_datasets=permitted_datasets)

    def get_gene_set(self, gene_sets_collection_id, gene_set_id,
                     gene_sets_types=[], permitted_datasets=None):
        gsc = self.get_gene_sets_collection(gene_sets_collection_id)
        if gsc is None:
            return None
        return gsc.get_gene_set(gene_set_id, gene_sets_types,
                                permitted_datasets=permitted_datasets)
