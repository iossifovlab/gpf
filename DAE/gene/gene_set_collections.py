'''
Created on Feb 16, 2017

@author: lubo
'''
from __future__ import print_function

import os
import traceback
import sqlite3
from itertools import groupby, chain
from collections import OrderedDict
import cPickle
import logging
from preloaded import register

# from denovo_gene_sets import build_denovo_gene_sets
from gene.config import GeneInfoConfig
from GeneTerms import loadGeneTerm, GeneTerms
from DAE import vDB
from pheno.pheno_regression import PhenoRegression

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

    def get_gene_sets_types_legend(self):
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


class DenovoGeneSetsType(object):

    def __init__(self, gene_term):
        self.gene_term = gene_term

    def get_gene_set_syms(self, gene_set_id, **kwargs):
        assert self.gene_term is not None

        if gene_set_id not in self.gene_term.t2G:
            LOGGER.warn("gene set {} not found...".format(gene_set_id))
            return set()
        syms = self.gene_term.t2G[gene_set_id].keys()
        return set(syms)

    def get_gene_sets(self):
        keys = self.gene_term.tDesc.keys()[:]
        keys = sorted(keys)
        return keys

class DenovoGeneSetsCollection(GeneInfoConfig):

    DATASETS_FACTORY = None

    def __init__(self):
        super(DenovoGeneSetsCollection, self).__init__()
        self.gsc_id = 'denovo'
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

        self.effect_types = [
            {'value': effect_type_arr[0], 'name' : effect_type_arr[1]}
            for effect_type_arr in map(
                lambda effect_type_str: effect_type_str.split(':'),
                self._get_att_list('effectTypes'))
        ]

        self.variant_criterias = []
        self.variant_criterias_names = set()
        for variant_criteria_id in self._get_att_list('variantCriterias'):
            source = self._get_att(
                'variantCriterias.{}.source'.format(variant_criteria_id))
            segments_arrs = map(
                lambda segment_str: segment_str.split(':'),
                self._get_att_list(
                    'variantCriterias.{}.segments'.format(
                        variant_criteria_id)))
            self.variant_criterias.append(
                [{
                    'property': source,
                    'name': segment_arr[0],
                    'value': segment_arr[1],
                    'type': segment_arr[2]
                 }
                 for segment_arr in segments_arrs]
            )
            self.variant_criterias_names.update([segment_arr[0]
                for segment_arr in segments_arrs])

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
            file = open(cache_file_path, 'r')
            self.cache = cPickle.load(file)
        else:
            self._generate_cache()
            file = open(cache_file_path, 'w')
            cPickle.dump(self.cache, file)

    def _generate_cache(self):
        for dataset in self._get_datasets():
            self._gene_sets_for(dataset)

    def _get_datasets(self):
        if self.DATASETS_FACTORY is None:
            self.DATASETS_FACTORY = register.get('datasets').get_factory()
        return [self.DATASETS_FACTORY.get_dataset(id)
                for id in self.datasets_pedigree_selectors.keys()]

    def get_gene_sets_types_legend(self):
        return [{
            'datasetId': dataset.dataset_id,
            'datasetName': dataset.descriptor['name'],
            'phenotypes': dataset.get_legend(
                pedigreeSelector=self.datasets_pedigree_selectors[dataset.dataset_id])
        } for dataset in self._get_datasets()]

    def get_gene_sets(self, gene_sets_types={'SD': ['autism']}, **kwargs):
        gene_sets_types_desc = '{}::{}'.format(
            ', '.join(set(gene_sets_types.keys())),
            ', '.join(set(chain(*gene_sets_types.values()))))
        result = []
        for gsn in self.gene_sets_names:
            gene_set_syms = set()
            for dataset_id, phenotypes in gene_sets_types.iteritems():
                gene_set_syms.update(
                    self._get_gene_set_syms(gsn, dataset_id, phenotypes))
            result.append({
                'name': gsn,
                'count': len(gene_set_syms),
                'syms': gene_set_syms,
                'desc': '{} ({})'.format(gsn, gene_sets_types_desc)
            })
        return result

    def get_gene_set(self, gene_set_id, gene_sets_types={'SD': ['autism']}, **kwargs):
        syms = self._get_gene_set_syms(gene_set_id, gene_sets_types)
        if not syms:
            return None

        return {
            "name": gene_set_id,
            "count": len(syms),
            "syms": syms,
            "desc": "{} ({})".format(gene_set_id, ";".join(gene_sets_types)),
        }

    def _get_gene_set_syms(self, name, dataset_id, phenotypes):
        criterias = name.split('.')
        effect_type = criterias[0]
        effect_type_subsets = self.cache[dataset_id][effect_type]

        variant_criterias = self.variant_criterias_names.intersection(criterias)
        other_criterias = set(criterias[1:]) - variant_criterias

        result = set()

        for _, phenotype_subsets in filter(
                lambda item: item[0] in phenotypes,
                effect_type_subsets.iteritems()):
            pheno_genes = set().union(*phenotype_subsets.values())
            for criteria in variant_criterias:
                pheno_genes &= phenotype_subsets.get(criteria, set())
            result |= pheno_genes

        for criteria in other_criterias:
            result &= effect_type_subsets.get(criteria, set())

        return result

    def _gene_sets_for(self, dataset):

        dataset_cache = {effect_type['name']:
                            {phenotype['id']: {}
                             for phenotype in dataset.get_legend()}
                         for effect_type in self.effect_types}
        self.cache[dataset.name] = dataset_cache
        pedigree_selector = self.datasets_pedigree_selectors[dataset.dataset_id]
        for effect_type in self.effect_types:
            variants = list(dataset.get_denovo_variants(
                effectTypes=effect_type['value']))
            effect_cache = dataset_cache[effect_type['name']]
            for criteria in chain(*self.variant_criterias):
                key = criteria['name']
                for variant in filter(lambda v: self._matches(v, dataset, criteria), variants):
                    gene_symbols = {ge['sym'] for ge in variant.requestedGeneEffects}
                    if 'sib' in variant.inChS:
                        effect_cache.setdefault('unaffected', {})\
                            .setdefault(key, set()).update(gene_symbols)
                    if 'prb' in variant.inChS:
                        family = dataset.families.get(variant.familyId, None)
                        if family is not None and \
                                pedigree_selector['source'] in family.atts:
                            effect_cache.setdefault(family.atts[pedigree_selector['source']], {})\
                                .setdefault(key, set()).update(gene_symbols)

            # recurrent / non recurrent
            gene_family_list = sorted(
                [(ge['sym'], v.familyId)
                 for v in variants for ge in v.requestedGeneEffects])
            gene_counts = {gene: len(set(gene_families))
                           for gene, gene_families
                           in groupby(gene_family_list, key=lambda x: x[0])}
            single = set()
            recurrent = set()
            for gene, count in gene_counts.iteritems():
                if count > 1:
                    recurrent.add(gene)
                else:
                    single.add(gene)
            effect_cache['Single'] = single
            effect_cache['Recurrent'] = recurrent

            # study type
            for variant in variants:
                study_type = variant.study.get_attr('study.type')
                effect_cache.setdefault(study_type, set())\
                    .update({ge['sym'] for ge in variant.requestedGeneEffects})

    @classmethod
    def _matches(cls, variant, dataset, criteria):
        prop = criteria['property']
        value = variant.get_attr(prop)
        if value is None:
            # check if it is a pheno criteria
            family = dataset.families.get(variant.familyId, None)
            if family is not None and prop in family.atts:
                value = family.atts[prop]
            else:
                return False
        cmp_value = criteria['value']
        criteria_type = criteria['type']

        if criteria_type == 'eq':
            return value == cmp_value
        elif criteria_type == 'neq':
            return value != cmp_value
        elif criteria_type == 'lt':
            return value < cmp_value
        elif criteria_type == 'gt':
            return value > cmp_value
        elif criteria_type == 'in':
            return cmp_value in value
        else:
            raise Exception('Unknown criteria type: {}'.format(criteria_type))

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

    def get_gene_sets_collections(self):
        if self.gene_sets_collections_desc:
            return self.gene_sets_collections_desc

        self.gene_sets_collections_desc = []
        for gsc_id in self.gene_info.getGeneTermIds():
            label = self.gene_info.getGeneTermAtt(gsc_id, "webLabel")
            formatStr = self.gene_info.getGeneTermAtt(gsc_id, "webFormatStr")
            if not label or not formatStr:
                continue
            gene_sets_types = []
            if gsc_id == 'denovo':
                gene_sets_types = self.get_gene_sets_collection(gsc_id)\
                    .get_gene_sets_types_legend()
            self.gene_sets_collections_desc.append(
                {
                    'desc': label,
                    'name': gsc_id,
                    'format': formatStr.split("|"),
                    'types': gene_sets_types,
                }
            )

        return self.gene_sets_collections_desc

    def has_gene_sets_collection(self, gsc_id):
        return any([
            gsc['name'] == gsc_id
            for gsc in self.get_gene_sets_collections()
        ])

    def get_gene_sets_collection(self, gene_sets_collection_id):
        if gene_sets_collection_id not in self.gene_sets_collections:
            gsc = register.get(gene_sets_collection_id)
            if gsc is None:
                gsc = GeneSetsCollection(gene_sets_collection_id)
                gsc.load()
            self.gene_sets_collections[gene_sets_collection_id] = gsc

        return self.gene_sets_collections.get(gene_sets_collection_id, None)

    def get_gene_sets(self, gene_sets_collection_id, gene_sets_types):
        gsc = self.get_gene_sets_collection(gene_sets_collection_id)
        if gsc is None:
            return None

        return gsc.get_gene_sets(gene_sets_types)

    def get_gene_set(
            self, gene_sets_collection_id, gene_set_id, gene_sets_types):
        gsc = self.get_gene_sets_collection(gene_sets_collection_id)
        if gsc is None:
            return None
        return gsc.get_gene_set(gene_set_id, gene_sets_types)
