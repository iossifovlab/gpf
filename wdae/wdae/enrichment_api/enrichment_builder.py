import abc
from collections.abc import Iterable
from typing import Any, Optional, Union, cast

from remote.rest_api_client import RESTClient
from studies.remote_study import RemoteGenotypeData
from studies.study_wrapper import RemoteStudyWrapper

from dae.enrichment_tool.enrichment_helper import EnrichmentHelper
from dae.person_sets import PersonSetCollection
from dae.studies.study import GenotypeData

from .enrichment_serializer import EnrichmentSerializer


class BaseEnrichmentBuilder:

    @abc.abstractmethod
    def build(self) -> list[dict[str, Any]]:
        raise NotImplementedError


class EnrichmentBuilder(BaseEnrichmentBuilder):
    """Build enrichment tool test."""

    def __init__(
        self, enrichment_helper: EnrichmentHelper,
        dataset: GenotypeData,
        gene_syms: Iterable[str],
        background_id: Optional[str],
        counting_id: Optional[str],
    ):
        self.enrichment_helper = enrichment_helper
        self.dataset = dataset
        self.gene_syms = gene_syms
        self.background_id = background_id
        self.counting_id = counting_id

        self.results: list[dict[str, Any]]
        enrichment_config = EnrichmentHelper.get_enrichment_config(dataset)
        assert enrichment_config is not None
        self.enrichment_config = enrichment_config

        self.person_set_collection = cast(
            PersonSetCollection,
            self.dataset.get_person_set_collection(
                self.enrichment_config["selected_person_set_collections"][0],
            ),
        )

    def build_results(self) -> list[dict[str, Any]]:
        """Build and return a list of enrichment results.

        Returns:
            A list of dictionaries representing the enrichment results.
        """
        results = []

        effect_types = self.enrichment_config["effect_types"]
        enrichment_result = self.enrichment_helper.calc_enrichment_test(
            self.dataset,
            self.person_set_collection.id,
            self.gene_syms,
            effect_types,
            self.background_id,
            self.counting_id,
        )
        for ps_id, effect_res in enrichment_result.items():
            res: dict[str, Any] = {}
            person_set = self.person_set_collection.person_sets[ps_id]
            children_stats = person_set.get_children_stats()
            res["childrenStats"] = {
                "M": children_stats.male,
                "F": children_stats.female,
                "U": children_stats.unspecified,
            }
            res["selector"] = person_set.name
            res["geneSymbols"] = list(self.gene_syms)
            res["peopleGroupId"] = self.person_set_collection.id
            res["peopleGroupValue"] = ps_id
            res["datasetId"] = self.dataset.study_id
            for effect_type, enrichement_res in effect_res.items():
                res[effect_type] = {}
                res[effect_type]["all"] = enrichement_res.all
                res[effect_type]["rec"] = enrichement_res.rec
                res[effect_type]["female"] = enrichement_res.female
                res[effect_type]["male"] = enrichement_res.male

            results.append(res)

        return results

    def build(self) -> list[dict[str, Any]]:
        results = self.build_results()

        serializer = EnrichmentSerializer(self.enrichment_config, results)
        results = serializer.serialize()

        self.results = results
        return self.results


class RemoteEnrichmentBuilder(BaseEnrichmentBuilder):
    """Builder for enrichment tool test for remote dataset."""

    def __init__(
        self, dataset: Union[RemoteGenotypeData, RemoteStudyWrapper],
        client: RESTClient,
        background_name: Optional[str],
        counting_name: Optional[str],
        gene_syms: Iterable[str],
    ):
        self.dataset = dataset
        self.client = client
        query: dict[str, Any] = {}
        query["datasetId"] = dataset._remote_study_id
        query["geneSymbols"] = list(gene_syms)
        query["enrichmentBackgroundModel"] = background_name
        query["enrichmentCountingModel"] = counting_name
        self.query = query

    def build(self) -> list[dict[str, Any]]:
        return cast(
            list[dict[str, Any]],
            self.client.post_enrichment_test(self.query)["result"],
        )
