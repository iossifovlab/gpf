from __future__ import print_function, absolute_import
from __future__ import unicode_literals

import json
from builtins import next
from builtins import str
import os
from itertools import chain, product
import logging

from variants.attributes import Inheritance, Status

LOGGER = logging.getLogger(__name__)


class DenovoGeneSetsCollection(object):

    def __init__(self, study, config):
        self.study = study
        self.config = config

        self.standard_criterias = self.config.standard_criterias
        self.recurrency_criterias = self.config.recurrency_criterias
        self.gene_sets_names = self.config.gene_sets_names
        if not self.config.denovo_gene_sets:
            return None
        self.denovo_gene_sets = self.config.denovo_gene_sets

        self.cache = {}

    def load(self, build_cache=False):
        if len(self.cache) == 0:
            self._load_cache_from_json(build_cache=build_cache)
        return DenovoGeneSetsCollection.get_gene_sets([self])

    def _load_cache_from_json(self, build_cache=False):
        for people_group_id, _ in self.denovo_gene_sets.items():
            cache_dir = self.config.denovo_gene_set_cache_file(people_group_id)
            if not os.path.exists(cache_dir):
                if not build_cache:
                    raise EnvironmentError(
                        "Denovo gene sets caches dir '{}' "
                        "does not exists".format(cache_dir))
                else:
                    self.build_cache([people_group_id])

            self.cache[people_group_id] = self._load_cache(cache_dir)

    def build_cache(self, people_group_ids=None):
        for people_group_id, _ in self.denovo_gene_sets.items():
            if people_group_ids and \
                    people_group_id not in people_group_ids:
                continue
            study_cache = self._generate_gene_sets_for(people_group_id)
            self._save_cache(people_group_id, study_cache)

    def _load_cache(self, cache_dir):
        with open(cache_dir, "r") as f:
            result = json.load(f)

        # change all list to sets so after loading from json
        result = self._convert_cache_innermost_types(result, list, set)

        return result

    def _save_cache(self, people_group_id, study_cache):
        # change all sets to lists so they can be saved in json
        cache = self._convert_cache_innermost_types(
            study_cache, set, list, sort_values=True)

        cache_dir = self.config.denovo_gene_set_cache_file(people_group_id)
        if not os.path.exists(os.path.dirname(cache_dir)):
            os.makedirs(os.path.dirname(cache_dir))
        with open(cache_dir, "w") as f:
            json.dump(
                cache, f, sort_keys=True, indent=4, separators=(',', ': '))

    def _convert_cache_innermost_types(
            self, cache, from_type, to_type, sort_values=False):
        if isinstance(cache, from_type):
            if sort_values is True:
                return sorted(to_type(cache))
            return to_type(cache)
        assert isinstance(cache, dict), \
            "expected type 'dict', got '{}'".format(type(cache))

        res = {}
        for key, value in cache.items():
            res[key] = self._convert_cache_innermost_types(
                value, from_type, to_type, sort_values=sort_values)

        return res

    def _generate_gene_sets_for(self, people_group_id):
        people_group = self.denovo_gene_sets[people_group_id]['source']

        people_group_values = [
            str(p) for p in self.study.get_pedigree_values(people_group)
        ]

        cache = {value: {} for value in people_group_values}

        variants = self.study.query_variants(
            inheritance=str(Inheritance.denovo.name),
            status='{} or {}'.format(
                Status.affected.name, Status.unaffected.name)
        )
        variants = list(variants)

        for criterias_combination in product(*self.standard_criterias):
            search_args = {criteria['property']: criteria['value']
                           for criteria in criterias_combination}
            for people_group_value in people_group_values:
                innermost_cache = self._init_criterias_cache(
                    cache[people_group_value], criterias_combination)
                innermost_cache.update(self._add_genes_families(
                    people_group, people_group_value, self.study, variants,
                    search_args))

        return cache

    @staticmethod
    def _init_criterias_cache(dataset_cache, criterias_combination):
        innermost_cache = dataset_cache
        for criteria in criterias_combination:
            innermost_cache = innermost_cache.setdefault(criteria['name'], {})

        return innermost_cache

    def get_gene_sets_legend(self, people_group_id):
        people_group_config = self.study.config.people_group_config
        if people_group_config is None:
            return []

        gene_sets_pg = people_group_config.get_people_group(people_group_id)
        if len(gene_sets_pg) == 0:
            return []

        return gene_sets_pg['domain']

    def get_gene_sets_types_legend(self):
        return [
            {
                'datasetId': self.study.id,
                'datasetName': self.study.name,
                'peopleGroupId': people_group_id,
                'peopleGroupName': people_group['name'],
                'peopleGroupLegend': self.get_gene_sets_legend(people_group_id)
            }
            for people_group_id, people_group in self.denovo_gene_sets.items()
        ]

    @staticmethod
    def _format_description(
            gene_sets_types, include_datasets_desc=False,
            full_description=True):
        if full_description:
            return ";".join([
                "{}:{}:{}".format(d, pg_id, ",".join(p))
                for d, pg in gene_sets_types.items() for pg_id, p in pg.items()
            ])

        people_groups = ', '.join(set(chain(*list([
            p for pg in gene_sets_types.values() for p in pg.values()]))))
        if include_datasets_desc:
            return '{}::{}'.format(
                ', '.join(set([
                    '{}:{}'.format(d, pg_id)
                    for d, pg in gene_sets_types.items()
                    for pg_id, _ in pg.items()])),
                people_groups)
        else:
            return people_groups

    @staticmethod
    def _get_gene_sets_names(dgsc):
        if len(dgsc) == 0:
            return []

        gene_sets_names = frozenset(dgsc[0].gene_sets_names)

        for d in dgsc:
            gene_sets_names = gene_sets_names.intersection(d.gene_sets_names)

        return list(gene_sets_names)

    @staticmethod
    def _get_recurrency_criterias(dgsc):
        if len(dgsc) == 0:
            return {}

        recurrency_criterias = dgsc[0].recurrency_criterias

        for d in dgsc:
            common_elements = frozenset(recurrency_criterias.keys()).\
                intersection(d.recurrency_criterias.keys())

            new_recurrency_criterias = {}
            for ce in common_elements:
                new_recurrency_criterias[ce] = {
                    'from': max(recurrency_criterias[ce]['from'],
                                d.recurrency_criterias[ce]['from']),
                    'to': min(recurrency_criterias[ce]['to'],
                              d.recurrency_criterias[ce]['to'])
                }

            recurrency_criterias = new_recurrency_criterias

        return recurrency_criterias

    @staticmethod
    def _get_cache(dgsc):
        cache = {}

        for d in dgsc:
            cache[d.study.id] = d.cache

        return cache

    @classmethod
    def get_gene_sets(
            cls, denovo_gene_sets_collections, gene_sets_types={}):
        gene_sets_types_desc = cls._format_description(gene_sets_types)

        result = []
        for gsn in cls._get_gene_sets_names(denovo_gene_sets_collections):
            gene_set_syms = cls._get_gene_set_syms(
                gsn, denovo_gene_sets_collections, gene_sets_types)
            if gene_set_syms:
                result.append({
                    'name': gsn,
                    'count': len(gene_set_syms),
                    'syms': gene_set_syms,
                    'desc': '{} ({})'.format(gsn, gene_sets_types_desc)
                })
        return result

    @classmethod
    def get_gene_set(
            cls, gene_set_id, denovo_gene_sets_collections,
            gene_sets_types={}):
        syms = cls._get_gene_set_syms(
            gene_set_id, denovo_gene_sets_collections, gene_sets_types)
        if not syms:
            return None

        return {
            "name": gene_set_id,
            "count": len(syms),
            "syms": syms,
            "desc": "{} ({})".format(
                gene_set_id,
                cls._format_description(gene_sets_types)
            )
        }

    @classmethod
    def _get_gene_set_syms(cls, gene_set_id, dgsc, gene_sets_types):
        rc = cls._get_recurrency_criterias(dgsc)
        criterias = set(gene_set_id.split('.'))
        recurrency_criterias = criterias & set(rc.keys())
        standard_criterias = criterias - recurrency_criterias
        if len(recurrency_criterias) > 0:
            recurrency_criteria = rc[next(iter(recurrency_criterias))]
        else:
            recurrency_criteria = None
        genes_families = {}
        for dataset_id, people_group in gene_sets_types.items():
            for people_group_id, people_group_values in \
                    people_group.items():
                for people_group_value in people_group_values:
                    ds_pedigree_genes_families = cls._get_gene_families(
                        cls._get_cache(dgsc),
                        {dataset_id, people_group_id, people_group_value}
                        | standard_criterias)
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
            cls, people_group, people_group_value, study, variants,
            search_args):
        cache = {}
        people_with_people_group = study.get_people_with_people_group(
            people_group, people_group_value)

        for variant in variants:
            family_id = variant.family_id
            for aa in variant.alt_alleles:
                if Inheritance.denovo not in aa.inheritance_in_members:
                    continue
                if not (set(aa.variant_in_members) & people_with_people_group):
                    continue

                filter_flag = False
                for search_arg_name, search_arg_value in search_args.items():
                    if search_arg_name == 'effect_types':
                        if not (aa.effect.types & set(search_arg_value)):
                            filter_flag = True
                            break
                    elif search_arg_name == 'sexes':
                        if not (set(aa.variant_in_sexes) &
                                set(search_arg_value)):
                            filter_flag = True
                            break

                if filter_flag:
                    continue

                effect = aa.effect
                for gene in effect.genes:
                    cache.setdefault(gene.symbol, set()).add(family_id)

        return cache
