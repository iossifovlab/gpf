from __future__ import annotations

import json
import logging
import os
from collections import defaultdict
from collections.abc import Collection, Iterable, Sequence
from itertools import product
from typing import Any

from dae.gene_sets.denovo_gene_sets_config import (
    DenovoGeneSetsConfig,
    DGSCQuery,
    RecurrencyCriteria,
    parse_denovo_gene_sets_study_config,
    parse_dgsc_query,
)
from dae.gene_sets.gene_sets_db import GeneSet
from dae.pedigrees.family import Person
from dae.person_sets import (
    PersonSetCollection,
)
from dae.studies.study import GenotypeData
from dae.variants.attributes import Inheritance

logger = logging.getLogger(__name__)


class DenovoGeneSetCollection:
    """Class representing a study's denovo gene sets."""

    def __init__(
        self,
        study_id: str,
        study_name: str,
        dgsc_config: DenovoGeneSetsConfig,
        pscs: dict[str, PersonSetCollection],
        *,
        cache: dict[str, Any] | None = None,
        gene_sets_types_legend: dict[str, Any] | None = None,
    ) -> None:
        self.study_id = study_id
        self.study_name = study_name

        self.config: DenovoGeneSetsConfig = dgsc_config

        self.recurrency_criteria = \
            self.config.recurrency
        self.gene_sets_ids = \
            self.config.gene_sets_ids

        self.pscs = pscs
        if cache is None:
            cache = self._build_empty_cache()
        self.cache: dict[str, Any] = cache
        self._gene_sets_types_legend: dict[
            str, Sequence[Collection[str]],
        ] | None = gene_sets_types_legend

    def add_gene(
        self,
        gene_effects: list[tuple[str, str]],
        persons: list[Person],
    ) -> None:
        """Add a gene to the cache."""
        for psc_id, person_set_collection in self.pscs.items():
            if psc_id not in self.cache:
                self.cache[psc_id] = {}
            for ps_id, person_set in person_set_collection.person_sets.items():
                for person in persons:
                    if person.fpid not in person_set.persons:
                        continue
                    for gene_symbol, effect in gene_effects:
                        self._cache_update(
                            psc_id, ps_id, gene_symbol, effect, person,
                        )

    def _build_empty_cache(self) -> dict[str, Any]:
        cache: dict[str, Any] = {}
        for psc_id in self.config.selected_person_set_collections:
            cache[psc_id] = {}
            for ps_id in self.pscs[psc_id].person_sets:
                cache[psc_id][ps_id] = {}

                ps_cache = cache[psc_id][ps_id]
                for effect_criteria, sex_critera in product(
                        self.config.effect_types.values(),
                        self.config.sexes.values()):
                    if effect_criteria.name not in ps_cache:
                        ps_cache[effect_criteria.name] = {}
                    effect_cache = ps_cache[effect_criteria.name]
                    if sex_critera.name not in effect_cache:
                        effect_cache[sex_critera.name] = {}

        return cache

    def _cache_update(
        self,
        psc_id: str,
        ps_id: str,
        gene_symbol: str,
        effect: str,
        person: Person,
    ) -> None:
        """Update the cache with a gene."""
        ps_cache = self.cache[psc_id][ps_id]
        for effect_criteria, sex_critera in product(
                self.config.effect_types.values(),
                self.config.sexes.values()):
            if effect not in effect_criteria.effects:
                continue
            if person.sex not in sex_critera.sexes:
                continue
            effect_cache = ps_cache[effect_criteria.name]
            sex_cache = effect_cache[sex_critera.name]
            if gene_symbol not in sex_cache:
                sex_cache[gene_symbol] = set()
            sex_cache[gene_symbol].add(person.family_id)

    @staticmethod
    def create_empty_collection(
        study: GenotypeData,
    ) -> DenovoGeneSetCollection | None:
        """Create an empty denovo gene set collection for a genotype data."""
        config = study.config
        assert config is not None, study.study_id
        dgsc_config = parse_denovo_gene_sets_study_config(
            study.config,
            has_denovo=study.has_denovo,
        )
        if dgsc_config is None:
            logger.info(
                "no denovo gene sets defined for %s", study.study_id)
            return None

        person_set_collections = {
            psc_id: psc
            for psc_id, psc in study.person_set_collections.items()
            if psc_id in dgsc_config.selected_person_set_collections
        }

        return DenovoGeneSetCollection(
            study.study_id,
            study.name,
            dgsc_config,
            person_set_collections,
        )

    @staticmethod
    def build_collection(
        genotype_data: GenotypeData,
    ) -> DenovoGeneSetCollection | None:
        """Generate a denovo gene set collection for a study."""
        dgsc = DenovoGeneSetCollection.create_empty_collection(genotype_data)
        if dgsc is None:
            return None

        assert dgsc is not None

        effect_types = [
            e
            for etc in dgsc.config.effect_types.values()
            for e in etc.effects
        ]
        variants = genotype_data.query_variants(
            effect_types=effect_types,
            inheritance=["denovo"],
            unique_family_variants=False,
        )

        for fv in variants:
            for fa in fv.family_alt_alleles:
                persons = []
                for index, person_id in enumerate(fa.variant_in_members):
                    if person_id is None:
                        continue
                    inheritance = fa.inheritance_in_members[index]
                    if inheritance != Inheritance.denovo:
                        continue
                    person = fa.family.persons[person_id]
                    persons.append(person)
                if not persons:
                    continue
                effect = fa.effects
                if effect is None:
                    continue
                gene_effects = [
                    (gene.symbol, gene.effect)
                    for gene in effect.genes
                    if gene.symbol is not None and gene.effect is not None
                ]
                assert all(
                    ge[0] is not None and ge[1] is not None
                    for ge in gene_effects)
                assert all(p is not None for p in persons)
                dgsc.add_gene(gene_effects, persons)
        return dgsc

    @staticmethod
    def _cache_file(
        psc_id: str,
        cache_dir: str,
    ) -> str:
        """Return the path to the cache file for a person set collection."""
        return os.path.join(
            cache_dir,
            f"denovo-cache-{psc_id}.json",
        )

    @classmethod
    def _convert_cache_innermost_types(
        cls, cache: Any,
        from_type: type,
        to_type: type, *,
        sort_values: bool = False,
    ) -> Any:
        """
        Coerce the types of all values in a dictionary matching a given type.

        This is done recursively.
        """
        if isinstance(cache, from_type):
            if sort_values is True:
                return sorted(to_type(cache))
            return to_type(cache)

        assert isinstance(
            cache, dict,
        ), f"expected type 'dict', got '{type(cache)}'"

        res = {}
        for key, value in cache.items():
            res[key] = cls._convert_cache_innermost_types(
                value, from_type, to_type, sort_values=sort_values,
            )
        return res

    def is_cached(self, cache_dir: str) -> bool:
        """Check if all the cache files exist."""
        for psc_id in self.config.selected_person_set_collections:
            cache_file = self._cache_file(psc_id, cache_dir)
            if not os.path.exists(cache_file):
                return False
        return True

    def save(self, cache_dir: str) -> None:
        """Save the denovo gene set collection to a cache files."""
        if not os.path.exists(cache_dir):
            os.mkdir(cache_dir)
        for psc_id in self.config.selected_person_set_collections:
            cache_file = self._cache_file(psc_id, cache_dir)
            content = self.cache[psc_id]
            content = self._convert_cache_innermost_types(
                content, set, list, sort_values=True)

            with open(cache_file, "w") as outfile:
                json.dump(content, outfile, sort_keys=True, indent=2)

    def load(self, cache_dir: str) -> None:
        """Load cached denovo gene set collection from a cache files."""
        for psc_id in self.config.selected_person_set_collections:
            cache_file = self._cache_file(psc_id, cache_dir)
            if not os.path.exists(cache_file):
                continue

            with open(cache_file, "r") as infile:
                cache = json.load(infile)
                self.cache[psc_id] = self._convert_cache_innermost_types(
                    cache, list, set,
                )

    def get_gene_sets_types_legend(self) -> dict[str, Any]:
        """Return dict with legends for each collection."""
        if self._gene_sets_types_legend is None:
            name = self.study_name or self.study_id
            person_set_collections = [
                {
                    "personSetCollectionId": collection_id,
                    "personSetCollectionName": person_set_collection.name,
                    "personSetCollectionLegend":
                        self.get_person_set_collection_legend(collection_id),
                }
                for collection_id, person_set_collection
                in self.pscs.items()
            ]
            self._gene_sets_types_legend = {
                "datasetId": self.study_id,
                "datasetName": name,
                "personSetCollections": person_set_collections,
            }

        return self._gene_sets_types_legend

    def get_person_set_collection_legend(
        self, psc_id: str,
    ) -> list[dict[str, Any]]:
        """Return the domain (used as a legend) of a person set collection."""
        # This could probably be removed, it just takes each domain
        # and returns a dict with a subset of the original keys
        person_set_collection = self.pscs.get(psc_id)
        if person_set_collection is not None:
            return person_set_collection.legend_json()
        return []

    def get_gene_set(
        self,
        dgsc_query: str | DGSCQuery,
    ) -> GeneSet | None:
        """Return a gene set from the collection."""
        if isinstance(dgsc_query, str):
            dgsc_query = parse_dgsc_query(dgsc_query, self.config)
        assert isinstance(dgsc_query, DGSCQuery)
        if dgsc_query.gene_set_id not in self.gene_sets_ids:
            raise ValueError(
                f"Invalid gene set id: {dgsc_query.gene_set_id}")
        if dgsc_query.psc_id not in self.config\
                .selected_person_set_collections:
            raise ValueError(
                f"Invalid person set collection id: {dgsc_query.psc_id}")
        result: dict[str, set[str]] = defaultdict(set)
        psc_cache = self.cache[dgsc_query.psc_id]
        for keys in product(
                    dgsc_query.selected_person_sets,
                    dgsc_query.effects,
                    dgsc_query.sex,
                ):
            innermost_cache = psc_cache[keys[0]][keys[1].name][keys[2].name]
            for gene, families in innermost_cache.items():
                result[gene].update(families)
        if dgsc_query.recurrency is not None:
            result = self._apply_recurrency(result, dgsc_query.recurrency)

        return GeneSet(
            name=str(dgsc_query),
            desc=str(dgsc_query),
            syms=list(result.keys()),
        )

    @classmethod
    def get_all_gene_sets(
        cls, denovo_gene_sets: list[DenovoGeneSetCollection],
        denovo_gene_set_spec: dict[str, dict[str, list[str]]],
    ) -> list[dict[str, Any]]:
        """Return all gene sets from provided denovo gene set collections."""
        sets = [
            cls.get_gene_set_from_collections(
                name,
                denovo_gene_sets,
                denovo_gene_set_spec)
            for name in cls._get_gene_sets_names(denovo_gene_sets)
        ]
        return list(filter(None, sets))

    @classmethod
    def get_gene_set_from_collections(
        cls, gene_set_id: str,
        denovo_gene_set_collections: list[DenovoGeneSetCollection],
        denovo_gene_set_spec: dict[str, dict[str, list[str]]],
    ) -> dict[str, Any] | None:
        """Return a single set from provided denovo gene set collections."""
        syms = cls._get_gene_set_syms(
            gene_set_id,
            denovo_gene_set_collections,
            denovo_gene_set_spec)
        if not syms:
            return None

        return {
            "name": gene_set_id,
            "count": len(syms),
            "syms": syms,
            "desc": f"{gene_set_id} "
            f"({cls._format_description(denovo_gene_set_spec)})",
        }

    @classmethod
    def _get_gene_set_syms(
        cls, gene_set_id: str,
        denovo_gene_set_collections: list[DenovoGeneSetCollection],
        denovo_gene_set_spec: dict[str, dict[str, list[str]]],
    ) -> set[str]:
        """
        Return symbols of all genes in a given gene set.

        Collect the symbols of all genes belonging to a
        given gene set from a number of denovo gene set collections,
        while filtering by the supplied spec.
        """
        criteria = set(gene_set_id.split("."))
        recurrency_criteria = cls._get_common_recurrency_criteria(
            denovo_gene_set_collections,
        )
        recurrency_criteria_names = criteria & set(recurrency_criteria.keys())
        standard_criteria = criteria - recurrency_criteria_names

        genes_families: dict[str, set[str]] = {}

        for dataset_id, person_set_collection in denovo_gene_set_spec.items():
            for (
                person_set_collection_id,
                person_set_collection_values,
            ) in person_set_collection.items():
                for value in person_set_collection_values:
                    all_criteria = standard_criteria.union(
                        (dataset_id, person_set_collection_id, value),
                    )

                    genes_to_families = cls._get_genes_to_families(
                        cls._get_cache(denovo_gene_set_collections),
                        all_criteria,
                    )

                    for gene, families in genes_to_families.items():
                        genes_families.setdefault(gene, set()).update(families)

        matching_genes = genes_families

        if recurrency_criteria_names:
            assert len(recurrency_criteria_names) == 1, gene_set_id
            recurrency_criterion = recurrency_criteria[
                recurrency_criteria_names.pop()
            ]
            matching_genes = cls._apply_recurrency(
                matching_genes, recurrency_criterion,
            )

        return set(matching_genes.keys())

    @classmethod
    def _get_genes_to_families(
        cls, gs_cache: dict[str, Any],
        criteria: Iterable[str],
    ) -> dict[str, set[str]]:
        """
        Recursively collect genes and families by given criteria.

        Collects all genes and their families which
        correspond to the set of given criteria.

        The input gs_cache must be nested dictionaries with
        leaf nodes of type 'set'.
        """
        if len(gs_cache) == 0:
            return {}
        gs_cache_keys = list(gs_cache.keys())
        criteria = set(criteria)
        next_keys = criteria.intersection(gs_cache_keys)

        if len(next_keys) == 0:
            result: dict[str, set[str]] = {}
            if not isinstance(gs_cache[gs_cache_keys[0]], set):
                # still not the end of the tree
                for key in gs_cache_keys:
                    for gene, families in cls._get_genes_to_families(
                        gs_cache[key], criteria,
                    ).items():
                        result.setdefault(gene, set()).update(families)
            elif len(criteria) == 0:
                # end of tree with satisfied criteria
                result.update(gs_cache)
            return result

        next_key = next_keys.pop()
        return cls._get_genes_to_families(
            gs_cache[next_key], criteria - {next_key},
        )

    @staticmethod
    def _get_common_recurrency_criteria(
        denovo_gene_set_collections: list[DenovoGeneSetCollection],
    ) -> dict[str, RecurrencyCriteria]:
        if len(denovo_gene_set_collections) == 0:
            return {}

        recurrency_criteria = \
            denovo_gene_set_collections[0].config.recurrency

        for collection in denovo_gene_set_collections:
            common_elements = frozenset(
                recurrency_criteria.keys(),
            ).intersection(collection.config.recurrency.keys())

            new_recurrency_criteria = {}
            for element in common_elements:
                new_recurrency_criteria[element] = recurrency_criteria[element]

            recurrency_criteria = new_recurrency_criteria

        return recurrency_criteria

    @staticmethod
    def _apply_recurrency(
        genes_to_families: dict[str, set[str]],
        recurrency: RecurrencyCriteria,
    ) -> dict[str, set[str]]:
        """Apply a recurrency criterion to a dictionary of genes."""

        if recurrency.end < 0:

            def filter_lambda(item: set[str]) -> bool:
                return len(item) >= recurrency.start

        else:

            def filter_lambda(item: set[str]) -> bool:
                return recurrency.start <= len(item) < recurrency.end

        return {
            k: v for k, v in genes_to_families.items() if filter_lambda(v)
        }

    @staticmethod
    def _get_cache(
        denovo_gene_set_collections: list[DenovoGeneSetCollection],
    ) -> dict[str, Any]:
        gs_cache = {}

        for collection in denovo_gene_set_collections:
            gs_cache[collection.study_id] = collection.cache

        return gs_cache

    @staticmethod
    def _format_description(
        denovo_gene_set_spec: dict[str, dict[str, list[str]]],
    ) -> str:
        return ";".join(
            [
                f"{genotype_data}:{group_id}:{','.join(values)}"
                for genotype_data, person_set_collection
                in denovo_gene_set_spec.items()
                for group_id, values in person_set_collection.items()
            ],
        )

    @staticmethod
    def _get_gene_sets_names(
        denovo_gene_set_collections: list[DenovoGeneSetCollection],
    ) -> list[str]:
        if len(denovo_gene_set_collections) == 0:
            return []

        gene_sets_ids = frozenset(
            denovo_gene_set_collections[0].gene_sets_ids,
        )

        for collection in denovo_gene_set_collections:
            gene_sets_ids = gene_sets_ids.intersection(
                collection.gene_sets_ids,
            )

        return list(gene_sets_ids)
