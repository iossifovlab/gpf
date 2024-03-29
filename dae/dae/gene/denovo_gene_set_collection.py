import logging
from itertools import chain


LOGGER = logging.getLogger(__name__)


class DenovoGeneSetCollection:
    """Class representing a study's denovo gene sets."""

    def __init__(self, study_id, study_name, config, person_set_collections):
        assert config.denovo_gene_sets is not None
        assert config.denovo_gene_sets.selected_person_set_collections

        self.study_id = study_id
        self.study_name = study_name
        self.config = config.denovo_gene_sets

        self.standard_criteria = self.config.standard_criterias
        self.recurrency_criteria = self.config.recurrency_criteria
        self.gene_sets_names = self.config.gene_sets_names

        self.person_set_collections = person_set_collections
        self.cache = {}
        self._gene_sets_types_legend = None

    def get_gene_sets_types_legend(self):
        """Return list of dictionaries for legends for each collection."""
        if self._gene_sets_types_legend is None:
            name = self.study_name if self.study_name else self.study_id
            # TODO Rename these dictionary keys accordingly
            self._gene_sets_types_legend = [
                {
                    "datasetId": self.study_id,
                    "datasetName": name,
                    "personSetCollectionId": collection_id,
                    "personSetCollectionName": person_set_collection["name"],
                    "personSetCollectionLegend":
                        self.get_person_set_collection_legend(collection_id),
                }
                for collection_id, person_set_collection
                in self.person_set_collections.items()
            ]

        return self._gene_sets_types_legend

    def get_person_set_collection_legend(self, person_set_collection_id):
        """Return the domain (used as a legend) of a person set collection."""
        # TODO This could probably be removed, it just takes each domain
        # and returns a dict with a subset of the original keys
        person_set_collection = self.person_set_collections.get(
            person_set_collection_id
        )
        if person_set_collection:
            return person_set_collection["domain"]
        return []

    @classmethod
    def get_all_gene_sets(cls, denovo_gene_sets, denovo_gene_set_spec=None):
        sets = [
            cls.get_gene_set(name, denovo_gene_sets, denovo_gene_set_spec)
            for name in cls._get_gene_sets_names(denovo_gene_sets)
        ]
        return list(filter(None, sets))

    @classmethod
    def get_gene_set(
            cls, gene_set_id, denovo_gene_set_collections,
            denovo_gene_set_spec=None):
        """Return a single set from provided denovo gene set collections."""
        syms = cls._get_gene_set_syms(
            gene_set_id, denovo_gene_set_collections, denovo_gene_set_spec)
        if not syms:
            return None

        return {
            "name": gene_set_id,
            "count": len(syms),
            "syms": syms,
            "desc": f"{gene_set_id} "
            f"({cls._format_description(denovo_gene_set_spec)})"
        }

    @classmethod
    def _get_gene_set_syms(
            cls, gene_set_id, denovo_gene_set_collections,
            denovo_gene_set_spec):
        """
        Return symbols of all genes in a given gene set.

        Collect the symbols of all genes belonging to a
        given gene set from a number of denovo gene set collections,
        while filtering by the supplied spec.
        """
        criteria = set(gene_set_id.split("."))
        recurrency_criteria = cls._get_recurrency_criteria(
            denovo_gene_set_collections
        )
        recurrency_criteria_names = criteria & set(recurrency_criteria.keys())
        standard_criteria = criteria - recurrency_criteria_names

        genes_families = {}
        for dataset_id, person_set_collection in denovo_gene_set_spec.items():
            for (
                person_set_collection_id,
                person_set_collection_values,
            ) in person_set_collection.items():
                for value in person_set_collection_values:
                    all_criteria = standard_criteria.union(
                        (dataset_id, person_set_collection_id, value)
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
            matching_genes = cls._apply_recurrency_criterion(
                matching_genes, recurrency_criterion
            )

        return set(matching_genes.keys())

    @classmethod
    def _get_genes_to_families(cls, gs_cache, criteria):
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
        next_keys = criteria.intersection(gs_cache_keys)

        if len(next_keys) == 0:
            result = {}
            if not isinstance(gs_cache[gs_cache_keys[0]], set):
                # still not the end of the tree
                for key in gs_cache_keys:
                    for gene, families in cls._get_genes_to_families(
                        gs_cache[key], criteria
                    ).items():
                        result.setdefault(gene, set()).update(families)
            elif len(criteria) == 0:
                # end of tree with satisfied criteria
                result.update(gs_cache)
            return result

        next_key = next_keys.pop()
        return cls._get_genes_to_families(
            gs_cache[next_key], criteria - {next_key}
        )

    @staticmethod
    def _narrowest_criteria(crit, left, right):
        return {
            "start": max(left[crit]["start"], getattr(right, crit).start),
            "end": max(left[crit]["end"], getattr(right, crit).end),
        }

    @staticmethod
    def _get_recurrency_criteria(denovo_gene_set_collections):
        if len(denovo_gene_set_collections) == 0:
            return {}

        recurrency_criteria = \
            denovo_gene_set_collections[0].recurrency_criteria.segments

        for collection in denovo_gene_set_collections:
            common_elements = frozenset(
                recurrency_criteria.keys()
            ).intersection(collection.recurrency_criteria.segments.keys())

            new_recurrency_criteria = {}
            for element in common_elements:
                new_recurrency_criteria[element] = \
                    DenovoGeneSetCollection._narrowest_criteria(
                        element,
                        recurrency_criteria,
                        collection.recurrency_criteria.segments)

            recurrency_criteria = new_recurrency_criteria

        return recurrency_criteria

    @staticmethod
    def _apply_recurrency_criterion(genes_to_families, recurrency_criterion):
        """Apply a recurrency criterion to a dictionary of genes."""
        assert isinstance(recurrency_criterion, dict)
        assert set(recurrency_criterion.keys()) == {
            "start",
            "end",
        }, recurrency_criterion

        if recurrency_criterion["end"] < 0:

            def filter_lambda(item):
                return len(item) >= recurrency_criterion["start"]

        else:

            def filter_lambda(item):
                return (
                    recurrency_criterion["start"]
                    <= len(item)
                    < recurrency_criterion["end"]
                )

        matching_genes = {
            k: v for k, v in genes_to_families.items() if filter_lambda(v)
        }

        return matching_genes

    @staticmethod
    def _get_cache(denovo_gene_set_collections):
        gs_cache = {}

        for collection in denovo_gene_set_collections:
            gs_cache[collection.study_id] = collection.cache

        return gs_cache

    @staticmethod
    def _format_description(
        denovo_gene_set_spec,
        include_datasets_desc=False,
        full_description=True,
    ):
        if full_description:
            return ";".join(
                [
                    f"{genotype_data}:{group_id}:{','.join(values)}"
                    for genotype_data, person_set_collection
                    in denovo_gene_set_spec.items()
                    for group_id, values in person_set_collection.items()
                ]
            )

        all_person_set_collection_values = ", ".join(
            set(
                chain(
                    *[
                        person_set_collection.values()
                        for person_set_collection
                        in denovo_gene_set_spec.values()
                    ]
                )
            )
        )

        if include_datasets_desc:
            datasets_desc = ", ".join(
                {
                    f"{genotype_data}:{person_set_collection_id}"
                    for genotype_data, person_set_collection
                    in denovo_gene_set_spec.items()
                    for person_set_collection_id
                    in person_set_collection
                }
            )
            return f"{datasets_desc}::{all_person_set_collection_values}"

        return all_person_set_collection_values

    @staticmethod
    def _get_gene_sets_names(denovo_gene_set_collections):
        if len(denovo_gene_set_collections) == 0:
            return []

        gene_sets_names = frozenset(
            denovo_gene_set_collections[0].gene_sets_names
        )

        for collection in denovo_gene_set_collections:
            gene_sets_names = gene_sets_names.intersection(
                collection.gene_sets_names
            )

        return list(gene_sets_names)
