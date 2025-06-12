import abc
from collections.abc import Iterable
from typing import Any, cast

from dae.enrichment_tool.enrichment_helper import EnrichmentHelper
from dae.enrichment_tool.enrichment_serializer import EnrichmentSerializer
from dae.person_sets import PersonSetCollection
from dae.studies.study import GenotypeData


class BaseEnrichmentBuilder:
    """Base class for enrichment builders."""
    def __init__(
        self, enrichment_helper: EnrichmentHelper, dataset: GenotypeData,
    ):
        self.enrichment_helper = enrichment_helper
        self.dataset = dataset
        enrichment_config = EnrichmentHelper.get_enrichment_config(
            dataset,
        )
        assert enrichment_config is not None
        self.enrichment_config = enrichment_config

    @abc.abstractmethod
    def build(
        self, gene_syms: Iterable[str],
        background_id: str | None, counting_id: str | None,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError


class EnrichmentBuilder(BaseEnrichmentBuilder):
    """Build enrichment tool test."""

    def __init__(
        self, enrichment_helper: EnrichmentHelper,
        dataset: GenotypeData,
    ):
        super().__init__(enrichment_helper, dataset)

        self.results: list[dict[str, Any]]

    def build_results(
        self, gene_syms: Iterable[str],
        background_id: str | None, counting_id: str | None,
    ) -> list[dict[str, Any]]:
        """Build and return a list of enrichment results.

        Returns:
            A list of dictionaries representing the enrichment results.
        """
        results = []

        person_set_collection = cast(
            PersonSetCollection,
            self.dataset.get_person_set_collection(
                self.enrichment_helper.get_selected_person_set_collections(
                    self.dataset),
            ),
        )

        effect_types = self.enrichment_config["effect_types"]
        enrichment_result = self.enrichment_helper.calc_enrichment_test(
            self.dataset,
            person_set_collection.id,
            gene_syms,
            effect_types,
            background_id=background_id,
            counter_id=counting_id,
        )
        for ps_id, effect_res in enrichment_result.items():
            res: dict[str, Any] = {}
            person_set = person_set_collection.person_sets[ps_id]
            children_stats = person_set.get_children_stats()
            res["childrenStats"] = {
                "M": children_stats.male,
                "F": children_stats.female,
                "U": children_stats.unspecified,
            }
            res["selector"] = person_set.name
            res["geneSymbols"] = list(gene_syms)
            res["peopleGroupId"] = person_set_collection.id
            res["peopleGroupValue"] = ps_id
            res["datasetId"] = self.dataset.study_id
            for effect_type, enrichment_res in effect_res.items():
                res[effect_type] = {}
                res[effect_type]["all"] = enrichment_res.all
                res[effect_type]["rec"] = enrichment_res.rec
                res[effect_type]["female"] = enrichment_res.female
                res[effect_type]["male"] = enrichment_res.male

            results.append(res)

        return results

    def build(
        self, gene_syms: Iterable[str],
        background_id: str | None, counting_id: str | None,
    ) -> list[dict[str, Any]]:
        results = self.build_results(gene_syms, background_id, counting_id)

        serializer = EnrichmentSerializer(self.enrichment_config, results)
        results = serializer.serialize()

        self.results = results
        return self.results
