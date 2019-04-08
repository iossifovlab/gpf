from __future__ import print_function, absolute_import
from __future__ import unicode_literals

import json
from builtins import next
from builtins import str
import os
import traceback
from itertools import chain, product
from collections import OrderedDict
import logging

from gene.config import GeneInfoConfig
from GeneTerms import loadGeneTerm
from variants.attributes import Inheritance, Status

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
                'count': len(list(self.gene_sets_collections.t2G[key].keys()))
            }
            for key, value in list(self.gene_sets_collections.tDesc.items())
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
            print("{} not found in {}".format(
                gene_set_id,
                self.gene_sets_collections.t2G.keys()))
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

    def __init__(self, collection_id, variants_db):
        super(DenovoGeneSetsCollection, self).__init__()

        self.variants_db = variants_db

        self.collection_id = collection_id
        self.cache = {}
        self._read_config()

    def _read_config(self):
        self.denovo_gene_sets = OrderedDict()
        for config in self.variants_db.get_all_configs():
            study_config = config.study_config

            pedigree_selector = self._get_att_from_config(
                study_config, 'pedigreeSelector')

            if not pedigree_selector:
                continue
            self.denovo_gene_sets[config.id] = {
                'source': pedigree_selector
            }

        self.standard_criterias = []
        for standard_criteria_id in self._get_att_list('standardCriterias'):
            segments_arrs = map(
                lambda segment_str: segment_str.split(':'),
                self._get_att_list('standardCriterias.{}.segments'.format(
                        standard_criteria_id)))
            self.standard_criterias.append(
                [{
                    'property': standard_criteria_id,
                    'name': segment_arr[0],
                    'value': segment_arr[1].split('.')
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

    def _get_att_from_config(self, config, att_name):
        gene_terms_section = config.get(
            'geneTerms.' + self.collection_id, None)
        if gene_terms_section:
            att = gene_terms_section.get(att_name, None)
            return att

    def _get_att_list_from_config(self, config, att_name):
        att = self._get_att(config, att_name)
        if att:
            return [a.strip() for a in att.split(',')]

    def _get_att_list(self, att_name):
        return self.gene_info.getGeneTermAttList(self.collection_id, att_name)

    def load(self, build_cache=False):
        if len(self.cache) == 0:
            self._load_cache_from_json(build_cache=build_cache)
        return self.get_gene_sets()

    def _load_cache_from_json(self, build_cache=False):
        studies = self._get_studies()
        for study in studies:
            cache_dir = study.gene_sets_cache_file()
            if not os.path.exists(cache_dir):
                if not build_cache:
                    raise EnvironmentError(
                        "Denovo gene sets caches dir '{}' "
                        "does not exists".format(cache_dir))
                else:
                    self.build_cache([study.id])

            self.cache[study.id] = self._load_cache(study)

    def build_cache(self, study_ids=None):
        for study in self._get_studies(study_ids):
            study_cache = self._generate_gene_sets_for(study)
            self._save_cache(study, study_cache)

    def _load_cache(self, study):
        cache_dir = study.gene_sets_cache_file()
        with open(cache_dir, "r") as f:
            result = json.load(f)

        # change all list to sets so after loading from json
        result = self._convert_cache_innermost_types(result, list, set)

        return result

    def _save_cache(self, study, study_cache):
        # change all sets to lists so they can be saved in json
        cache = self._convert_cache_innermost_types(study_cache, set, list)

        cache_dir = study.gene_sets_cache_file()
        if not os.path.exists(os.path.dirname(cache_dir)):
            os.makedirs(os.path.dirname(cache_dir))
        with open(cache_dir, "w") as f:
            json.dump(
                cache, f, sort_keys=True, indent=4, separators=(',', ': '))

    def _convert_cache_innermost_types(self, cache, from_type, to_type):
        if isinstance(cache, from_type):
            return to_type(cache)
        assert isinstance(cache, dict), \
            "expected type 'dict', got '{}'".format(type(cache))

        res = {}
        for key, value in cache.items():
            res[key] = self._convert_cache_innermost_types(
                value, from_type, to_type)

        return res

    def _generate_gene_sets_for(self, study):
        pedigree_selector = self.denovo_gene_sets[study.id]['source']
        pedigree_selector_values = [
            str(p) for p in study.get_pedigree_values(pedigree_selector)
        ]

        cache = {value: {} for value in pedigree_selector_values}

        for criterias_combination in product(
                *self.standard_criterias):
            search_args = {criteria['property']: criteria['value']
                           for criteria in criterias_combination}
            for pedigree_selector_value in pedigree_selector_values:
                innermost_cache = self._init_criterias_cache(
                    cache[pedigree_selector_value],
                    criterias_combination)
                innermost_cache.update(self._add_genes_families(
                    pedigree_selector, pedigree_selector_value, study,
                    search_args))

        return cache

    @staticmethod
    def _init_criterias_cache(dataset_cache, criterias_combination):
        innermost_cache = dataset_cache
        for criteria in criterias_combination:
            innermost_cache = \
                innermost_cache.setdefault(criteria['name'], {})

        return innermost_cache

    def _get_studies(self, datasets_ids=None):
        if datasets_ids is None:
            datasets_ids = self.get_study_ids()
        return [
            self.variants_db.get_wdae_wrapper(dataset_id)
            for dataset_id in datasets_ids
        ]

    def get_study_ids(self):
        return self.denovo_gene_sets.keys()

    def get_gene_sets_types_legend(self, permitted_datasets=None):
        return [
            {
                'datasetId': study.id,
                'datasetName': study.name,
                'phenotypes': study.get_legend()
            }
            for study in self._get_studies()
            if permitted_datasets is None or
            study.id in permitted_datasets
        ]

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

        pedigree_selectors = ', '.join(
            set(chain(*list(gene_sets_types.values()))))
        if include_datasets_desc:
            return '{}::{}'.format(
                ', '.join(set(gene_sets_types.keys())),
                pedigree_selectors)
        else:
            return pedigree_selectors

    def get_gene_sets(
            self, gene_sets_types={'f1_group': ['autism']}, **kwargs):
        gene_sets_types = self._filter_gene_sets_types(
            gene_sets_types,
            kwargs.get('permitted_datasets', None))
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

        # print("genes_families", genes_families)
        matching_genes = genes_families
        if recurrency_criteria:
            # print("recurrency_criteria", recurrency_criteria)
            if recurrency_criteria['to'] < 0:
                def filter_lambda(item): return len(
                    item) >= recurrency_criteria['from']
            else:
                def filter_lambda(item):
                    return recurrency_criteria['from'] <= len(item) \
                           < recurrency_criteria['to']

            matching_genes = {
                k: v
                for k, v in genes_families.items()
                if filter_lambda(v)
            }

        matching_genes = matching_genes.keys()
        # print("matching_genes", matching_genes)

        return set(matching_genes)

    @classmethod
    def _get_gene_families(cls, cache, criterias):
        if len(cache) == 0:
            return {}
        cache_keys = list(cache.keys())
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

    @classmethod
    def _add_genes_families(
            cls, phenotype_column, phenotype, study, search_args):
        cache = {}
        affected_people = DenovoGeneSetsCollection._get_affected_people(
            study, phenotype_column, phenotype)
        variants = study.query_variants(
                inheritance=str(Inheritance.denovo.name),
                status='{} or {}'.format(
                    Status.affected.name, Status.unaffected.name),
                person_ids=list(affected_people),
                **search_args)

        # variants = list(variants)
        # print("Variants count:", len(variants), "search args:", search_args)

        for variant in variants:
            family_id = variant.family_id
            for allele in variant.alt_alleles:
                effect = allele.effect
                for gene in effect.genes:
                    cache.setdefault(gene.symbol, set()).add(family_id)

        return cache

    @staticmethod
    def _get_affected_people(study, phenotype_column, phenotype):
        affected_person_ids = set()
        for study in study.studies:
            pedigree_df = study.backend.ped_df
            people_ids = pedigree_df[
                pedigree_df[phenotype_column] == phenotype]
            affected_person_ids.update(people_ids['person_id'])

        return affected_person_ids


class GeneSetsCollections(object):

    def __init__(self, variants_db, config=None):
        if config is None:
            config = GeneInfoConfig()

        self.config = config
        self.variants_db = variants_db
        self.gene_sets_collections = {}

    def get_collections_descriptions(self, permitted_datasets=None):
        gene_sets_collections_desc = []
        for gsc_id in self.config.gene_info.getGeneTermIds():
            label = self.config.gene_info.getGeneTermAtt(gsc_id, "webLabel")
            formatStr = self.config.gene_info.getGeneTermAtt(
                gsc_id, "webFormatStr")
            if not label or not formatStr:
                continue
            gene_sets_types = self.get_gene_sets_collection(gsc_id) \
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
            for gsc in self.get_collections_descriptions()
        ])

    def _load_gene_sets_collection(self, gene_sets_collection_id, load=True):
        if gene_sets_collection_id == 'denovo':
            gsc = DenovoGeneSetsCollection(
                gene_sets_collection_id,
                variants_db=self.variants_db)
        else:
            gsc = GeneSetsCollection(gene_sets_collection_id)

        if load:
            gsc.load()

        return gsc

    def get_gene_sets_collection(self, gene_sets_collection_id, load=True):
        if gene_sets_collection_id not in self.gene_sets_collections:
            gsc = self._load_gene_sets_collection(
                gene_sets_collection_id, load)
            self.gene_sets_collections[gene_sets_collection_id] = gsc

        return self.gene_sets_collections.get(gene_sets_collection_id, None)

    def get_gene_sets(self, gene_sets_collection_id, gene_sets_types=[],
                      permitted_datasets=None, load=True):
        gsc = self.get_gene_sets_collection(gene_sets_collection_id, load)
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
