import json
import os
from itertools import product

from dae.variants.attributes import Inheritance
from dae.gene.denovo_gene_set_collection import DenovoGeneSetCollection
from dae.variants.attributes import Sex
from dae.utils.effect_utils import expand_effect_types


class DenovoGeneSetCollectionFactory:

    @staticmethod
    def denovo_gene_set_cache_file(config, person_set_collection_id=""):
        cache_path = os.path.join(
            config.conf_dir,
            "denovo-cache-" + person_set_collection_id + ".json",
        )

        return cache_path

    @classmethod
    def load_collection(cls, genotype_data_study):
        """Load a denovo gene set collection for a given study."""
        config = genotype_data_study.config
        assert config is not None, genotype_data_study.id
        selected_person_set_collections = \
            config.denovo_gene_sets.selected_person_set_collections
        person_set_collection_configs = {
            psc.id: psc.config_json()
            for psc in genotype_data_study.person_set_collections.values()
            if psc.id in selected_person_set_collections
        }
        collection = DenovoGeneSetCollection(
            genotype_data_study.study_id, genotype_data_study.name, config,
            dict(person_set_collection_configs.items()))

        for (
            person_set_collection_id
        ) in config.denovo_gene_sets.selected_person_set_collections:
            cache_dir = cls.denovo_gene_set_cache_file(
                config, person_set_collection_id
            )
            if not os.path.exists(cache_dir):
                raise EnvironmentError(
                    f"Denovo gene sets caches dir '{cache_dir}' "
                    f"does not exists"
                )

            with open(cache_dir, "r") as f:
                contents = json.load(f)
            # change all list to sets after loading from json
            contents = cls._convert_cache_innermost_types(contents, list, set)
            collection.cache[person_set_collection_id] = contents
        return collection

    @classmethod
    def build_collection(cls, genotype_data_study):
        """Build a denovo gene set collection for a study and save it."""
        config = genotype_data_study.config
        assert config is not None, genotype_data_study.id

        denovo_person_set_collections = \
            config.denovo_gene_sets.selected_person_set_collections
        for person_set_collection_id in denovo_person_set_collections:
            gene_set_cache = cls._generate_gene_set_for(
                genotype_data_study,
                config.denovo_gene_sets,
                person_set_collection_id,
            )
            cache_path = cls.denovo_gene_set_cache_file(
                config, person_set_collection_id
            )
            cls._save_cache(gene_set_cache, cache_path)

    @classmethod
    def _format_criterias(cls, standard_criterias):
        """
        Replicates functionality from denovo gene set config parser.
        Given a TOML config's standard criterias, it does additional formatting
        which was done before in the parser.
        """

        effect_type_criterias = []
        for name, criteria in standard_criterias.effect_types.segments.items():
            effect_type_criterias.append(
                {
                    "property": "effect_types",
                    "name": name,
                    "value": expand_effect_types(criteria),
                }
            )
        sex_criterias = []
        for name, criteria in standard_criterias.sexes.segments.items():
            sex_criterias.append(
                {
                    "property": "sexes",
                    "name": name,
                    "value": [Sex.from_name(criteria)],
                }
            )
        return (effect_type_criterias, sex_criterias)

    @classmethod
    def _generate_gene_set_for(
            cls, genotype_data, config, person_set_collection_id):
        """
        Produces a nested dictionary which represents a denovo gene set.
        It maps denovo gene set criteria to an innermost dictionary mapping
        gene set symbols to lists of family IDs.
        """
        person_set_collection = genotype_data.get_person_set_collection(
            person_set_collection_id
        )

        cache = {
            set_id: {} for set_id in person_set_collection.person_sets.keys()
        }

        variants = list(
            genotype_data.query_variants(inheritance=["denovo"]))

        criterias = product(*cls._format_criterias(config.standard_criterias))

        for criteria_combination in criterias:
            search_args = {
                criteria["property"]: criteria["value"]
                for criteria in criteria_combination
            }
            for person_set in person_set_collection.person_sets.values():
                innermost_cache = cache[person_set.id]
                for criteria in criteria_combination:
                    innermost_cache = innermost_cache.setdefault(
                        criteria["name"], {}
                    )

                persons_in_set = set(person_set.persons.keys())
                innermost_cache.update(
                    cls._add_genes_families(
                        variants, persons_in_set, search_args
                    )
                )

        return cache

    @classmethod
    def _save_cache(cls, cache, cache_path):
        """
        Write a denovo gene set cache to the filesystem in JSON format.
        """
        # change all sets to lists so they can be saved in json
        cache = cls._convert_cache_innermost_types(
            cache, set, list, sort_values=True
        )

        if not os.path.exists(os.path.dirname(cache_path)):
            os.makedirs(os.path.dirname(cache_path))
        with open(cache_path, "w") as f:
            json.dump(
                cache, f, sort_keys=True, indent=4, separators=(",", ": ")
            )

    @classmethod
    def _convert_cache_innermost_types(
        cls, cache, from_type, to_type, sort_values=False
    ):
        """
        Recursively coerce all values of a given type in a dictionary
        to another type.
        """
        if isinstance(cache, from_type):
            if sort_values is True:
                return sorted(to_type(cache))
            return to_type(cache)

        assert isinstance(
            cache, dict
        ), "expected type 'dict', got '{}'".format(type(cache))

        res = {}
        for key, value in cache.items():
            res[key] = cls._convert_cache_innermost_types(
                value, from_type, to_type, sort_values=sort_values
            )

        return res

    @staticmethod
    def _add_genes_families(variants, persons_in_set, search_args):
        """
        For the given variants and people with a certain people group,
        produce a dictionary which maps the gene symbols of those variants
        matching the given search_args to the IDs of the families in which
        those variants are found.
        """
        cache = {}

        for variant in variants:
            family_id = variant.family_id
            for aa in variant.alt_alleles:
                if Inheritance.denovo not in aa.inheritance_in_members:
                    continue
                if not (set(aa.variant_in_members) & persons_in_set):
                    continue

                filter_flag = False
                for search_arg_name, search_arg_value in search_args.items():
                    if search_arg_name == "effect_types":
                        # FIXME: Avoid conversion of effect types to set
                        if not (
                            aa.effects
                            and set(aa.effects.types) & set(search_arg_value)
                        ):
                            filter_flag = True
                            break
                    elif search_arg_name == "sexes":
                        if not (
                            set(aa.variant_in_sexes) & set(search_arg_value)
                        ):
                            filter_flag = True
                            break

                if filter_flag:
                    continue

                effect = aa.effects
                for gene in effect.genes:
                    if gene.effect in search_args.get("effect_types", set()):
                        cache.setdefault(gene.symbol, set()).add(family_id)

        return cache
