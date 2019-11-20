import json
import os
from itertools import chain, product
import logging

from dae.gene.denovo_gene_set_config import DenovoGeneSetConfigParser

from dae.variants.attributes import Inheritance

LOGGER = logging.getLogger(__name__)


class DenovoGeneSetCollection(object):

    def __init__(self, study, config):
        self.study = study
        self.config = config

        self.standard_criterias = self.config.standard_criterias
        self.recurrency_criterias = self.config.recurrency_criterias
        self.gene_sets_names = self.config.gene_sets_names
        if not self.config.people_groups:
            return None
        self.people_groups = self.config.people_groups

        self.cache = {}

    def load(self, build_cache=False):
        if len(self.cache) == 0:
            self._load_cache_from_json(build_cache=build_cache)
        return DenovoGeneSetCollection.get_gene_sets([self])

    def _load_cache_from_json(self, build_cache=False):
        for people_group_id in self.people_groups:
            cache_dir = DenovoGeneSetConfigParser.denovo_gene_set_cache_file(
                self.config, people_group_id
            )
            if not os.path.exists(cache_dir):
                if not build_cache:
                    raise EnvironmentError(
                        "Denovo gene sets caches dir '{}' "
                        "does not exists".format(cache_dir))
                else:
                    self.build_cache([people_group_id])

            self.cache[people_group_id] = self._load_cache(cache_dir)

    def build_cache(self, people_group_ids=None):
        for people_group_id in self.people_groups:
            if people_group_ids and \
                    people_group_id not in people_group_ids:
                continue
            study_cache = self._generate_gene_set_for(people_group_id)
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

        cache_dir = DenovoGeneSetConfigParser.denovo_gene_set_cache_file(
            self.config, people_group_id
        )
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

    def _generate_gene_set_for(self, people_group_id):
        people_group_source = self.people_groups[people_group_id]['source']
        people_group_values = [
            str(p) for p in self.study.get_pedigree_values(people_group_source)
        ]

        cache = {value: {} for value in people_group_values}

        variants = self.study.query_variants(
            inheritance=str(Inheritance.denovo.name)
        )
        variants = list(variants)

        for criterias_combination in product(*self.standard_criterias):
            search_args = {criteria['property']: criteria['value']
                           for criteria in criterias_combination}
            for people_group_value in people_group_values:
                innermost_cache = self._init_criterias_cache(
                    cache[people_group_value], criterias_combination)
                innermost_cache.update(self._add_genes_families(
                    people_group_id, people_group_value, self.study, variants,
                    search_args))

        return cache

    @staticmethod
    def _init_criterias_cache(dataset_cache, criterias_combination):
        innermost_cache = dataset_cache
        for criteria in criterias_combination:
            innermost_cache = innermost_cache.setdefault(criteria['name'], {})

        return innermost_cache

    def get_gene_set_legend(self, people_group_id):
        gene_set_pg = self.study.get_people_group(people_group_id)
        if not gene_set_pg:
            return []

        return list(gene_set_pg['domain'].values())

    def get_gene_sets_types_legend(self):
        return [
            {
                'datasetId': self.study.id,
                'datasetName': self.study.name,
                'peopleGroupId': people_group_id,
                'peopleGroupName': people_group['name'],
                'peopleGroupLegend': self.get_gene_set_legend(people_group_id)
            }
            for people_group_id, people_group in self.people_groups.items()
        ]

    @staticmethod
    def _format_description(
            denovo_gene_set_spec, include_datasets_desc=False,
            full_description=True):

        if full_description:
            return ';'.join([
                '{}:{}:{}'.format(genotype_data, group_id, ','.join(values))
                for genotype_data, people_group in denovo_gene_set_spec.items()
                for group_id, values in people_group.items()
            ])

        all_people_group_values = ', '.join(set(chain(
            *[people_group.values()
              for people_group in denovo_gene_set_spec.values()])
        ))

        if include_datasets_desc:
            return '{}::{}'.format(
                ', '.join(set([
                    f'{genotype_data}:{people_group_id}'
                    for genotype_data, people_group
                    in denovo_gene_set_spec.items()
                    for people_group_id in people_group])
                ),
                all_people_group_values)
        else:
            return all_people_group_values

    @staticmethod
    def _get_gene_sets_names(dgs):
        if len(dgs) == 0:
            return []

        gene_sets_names = frozenset(dgs[0].gene_sets_names)

        for d in dgs:
            gene_sets_names = gene_sets_names.intersection(d.gene_sets_names)

        return list(gene_sets_names)

    @staticmethod
    def _get_recurrency_criterias(dgs):
        if len(dgs) == 0:
            return {}

        recurrency_criterias = dgs[0].recurrency_criterias

        for d in dgs:
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
    def _get_cache(dgs):
        cache = {}

        for d in dgs:
            cache[d.study.id] = d.cache

        return cache

    @classmethod
    def get_gene_sets(cls, denovo_gene_sets, denovo_gene_set_spec={}):
        sets = [
            DenovoGeneSetCollection.get_gene_set(
                name, denovo_gene_sets, denovo_gene_set_spec
            )
            for name in cls._get_gene_sets_names(denovo_gene_sets)
        ]
        return list(filter(None, sets))

    @classmethod
    def get_gene_set(
            cls, gene_set_id, denovo_gene_sets, denovo_gene_set_spec={}):
        syms = cls._get_gene_set_syms(
            gene_set_id, denovo_gene_sets, denovo_gene_set_spec)
        if not syms:
            return None

        return {
            "name": gene_set_id,
            "count": len(syms),
            "syms": syms,
            "desc": "{} ({})".format(
                gene_set_id,
                cls._format_description(denovo_gene_set_spec)
            )
        }

    @classmethod
    def _get_gene_set_syms(cls, gene_set_id, dgs, denovo_gene_set_spec):
        rc = cls._get_recurrency_criterias(dgs)
        criterias = set(gene_set_id.split('.'))
        recurrency_criterias = criterias & set(rc.keys())
        standard_criterias = criterias - recurrency_criterias
        if len(recurrency_criterias) > 0:
            recurrency_criteria = rc[next(iter(recurrency_criterias))]
        else:
            recurrency_criteria = None
        genes_families = {}
        for dataset_id, people_group in denovo_gene_set_spec.items():
            for people_group_id, people_group_values in \
                    people_group.items():
                for people_group_value in people_group_values:
                    ds_pedigree_genes_families = cls._get_gene_families(
                        cls._get_cache(dgs),
                        {dataset_id, people_group_id, people_group_value}
                        | standard_criterias)
                    for gene, families in ds_pedigree_genes_families.items():
                        genes_families.setdefault(gene, set()).update(families)

        matching_genes = genes_families
        if recurrency_criteria:
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
                    if gene.effect in search_args.get('effect_types', set()):
                        cache.setdefault(gene.symbol, set()).add(family_id)

        return cache
