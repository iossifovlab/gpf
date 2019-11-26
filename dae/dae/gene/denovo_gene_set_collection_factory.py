import json
import os
from itertools import product
from functools import reduce

from dae.variants.attributes import Inheritance
from dae.gene.denovo_gene_set_config import DenovoGeneSetConfigParser
from dae.gene.denovo_gene_set_collection import DenovoGeneSetCollection


class DenovoGeneSetCollectionFactory():

    @classmethod
    def load_collection(cls, study, config):
        '''
        Loads a denovo gene set collection (from the filesystem)
        specified by a denovo gene set config.
        '''
        collection = DenovoGeneSetCollection(study.id, study.name, config)
        for people_group_id in config.people_groups:
            cache_dir = DenovoGeneSetConfigParser.denovo_gene_set_cache_file(
                config, people_group_id
            )
            if not os.path.exists(cache_dir):
                raise EnvironmentError(
                    "Denovo gene sets caches dir '{}' "
                    "does not exists".format(cache_dir))

            with open(cache_dir, "r") as f:
                contents = json.load(f)
            # change all list to sets after loading from json
            contents = cls._convert_cache_innermost_types(contents, list, set)
            collection.cache[people_group_id] = contents
        return collection

    @classmethod
    def build_collection(cls, config):
        '''
        Builds a denovo gene set collection specified by
        a denovo gene set config and writes it to the filesystem.
        '''
        for people_group_id in config.people_groups:
            gene_set_cache = cls._generate_gene_set_for(people_group_id)
            cache_path = DenovoGeneSetConfigParser.denovo_gene_set_cache_file(
                config, people_group_id
            )
            cls._save_cache(gene_set_cache, cache_path)

    @classmethod
    def _generate_gene_set_for(cls, study, config, people_group_id):
        '''
        Produces a nested dictionary which represents a denovo gene set.
        It maps denovo gene set criteria to an innermost dictionary mapping
        gene set symbols to lists of family IDs.
        '''
        people_group_source = config.people_groups[people_group_id]['source']
        people_group_values = [
                str(p) for p in study.get_pedigree_values(people_group_source)
        ]

        cache = {value: {} for value in people_group_values}

        variants = list(study.query_variants(
            inheritance=str(Inheritance.denovo.name)
        ))

        for criteria_combination in product(*config.standard_criterias):

            # Skip criteria combinations which are not
            # selected in the denovo gene set configuration.
            criteria_string = \
                str(reduce(lambda x, y: f'{x}.{y}', criteria_combination))
            if criteria_string not in config.gene_sets_names:
                continue

            search_args = {criteria['property']: criteria['value']
                           for criteria in criteria_combination}
            for people_group_value in people_group_values:
                innermost_cache = cache[people_group_value]
                for criteria in criteria_combination:
                    innermost_cache = innermost_cache.setdefault(
                        criteria['name'], {}
                    )

                people_with_people_group = study.get_people_with_people_group(
                    people_group_id, people_group_value
                )

                innermost_cache.update(cls._add_genes_families(
                    variants, people_with_people_group, search_args)
                )

        return cache

    @classmethod
    def _save_cache(cls, cache, cache_path):
        '''
        Write a denovo gene set cache to the filesystem in JSON format.
        '''
        # change all sets to lists so they can be saved in json
        cache = cls._convert_cache_innermost_types(
            cache, set, list, sort_values=True)

        if not os.path.exists(os.path.dirname(cache_path)):
            os.makedirs(os.path.dirname(cache_path))
        with open(cache_path, "w") as f:
            json.dump(cache, f, sort_keys=True, indent=4,
                      separators=(',', ': '))

    @classmethod
    def _convert_cache_innermost_types(cls, cache, from_type, to_type,
                                       sort_values=False):
        '''
        Recursively coerce all values of a given type in a dictionary
        to another type.
        '''
        if isinstance(cache, from_type):
            if sort_values is True:
                return sorted(to_type(cache))
            return to_type(cache)

        assert isinstance(cache, dict), \
            "expected type 'dict', got '{}'".format(type(cache))

        res = {}
        for key, value in cache.items():
            res[key] = cls._convert_cache_innermost_types(
                value, from_type, to_type, sort_values=sort_values
            )

        return res

    @staticmethod
    def _add_genes_families(variants, people_with_people_group, search_args):
        '''
        For the given variants and people with a certain people group,
        produce a dictionary which maps the gene symbols of those variants
        matching the given search_args to the IDs of the families in which
        those variants are found.
        '''
        cache = {}

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
