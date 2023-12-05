import abc
from typing import Any, Optional, Iterable, cast, Union

from remote.rest_api_client import RESTClient
from studies.remote_study import RemoteGenotypeData
from studies.study_wrapper import RemoteStudyWrapper

from dae.studies.study import GenotypeData
from dae.enrichment_tool.genotype_helper import GenotypeHelper
from dae.enrichment_tool.enrichment_helper import EnrichmentHelper
from dae.enrichment_tool.tool import EnrichmentTool

from dae.effect_annotation.effect import expand_effect_types
from dae.person_sets import PersonSet, PersonSetCollection

from .enrichment_serializer import EnrichmentSerializer


class BaseEnrichmentBuilder:

    @abc.abstractmethod
    def build(self) -> list[dict[str, Any]]:
        raise NotImplementedError()


class EnrichmentBuilder(BaseEnrichmentBuilder):
    """Build enrichment tool test."""

    def __init__(
            self, dataset: GenotypeData,
            enrichment_tool: EnrichmentTool,
            gene_syms: Iterable[str]):
        self.dataset = dataset
        self.gene_syms = gene_syms
        self.tool = enrichment_tool
        self.results: list[dict[str, Any]]
        enrichment_config = EnrichmentHelper.get_enrichment_config(dataset)
        assert enrichment_config is not None
        self.enrichment_config = enrichment_config

        effect_types = expand_effect_types(
            self.enrichment_config["effect_types"])

        self.person_set_collection = cast(
            PersonSetCollection,
            self.dataset.get_person_set_collection(
                self.enrichment_config["selected_person_set_collections"][0]
            )
        )

        self.helper = GenotypeHelper(
            self.dataset, self.person_set_collection,
            effect_types=effect_types)

    def build_people_group_selector(
        self, effect_types: list[str], person_set: PersonSet
    ) -> Optional[dict[str, Any]]:
        """Construct people group selector."""
        children_stats = self.helper.get_children_stats(person_set.id)
        children_count = (
            children_stats.male
            + children_stats.female
            + children_stats.unspecified
        )

        if children_count <= 0:
            return None

        results: dict[str, Any] = {}
        for effect_type in effect_types:
            enrichment_results = self.tool.calc(
                self.gene_syms,
                self.helper.get_denovo_events(),
                effect_types=[effect_type],
                children_by_sex=self.helper.children_by_sex(person_set.id)
            )

            results[effect_type] = enrichment_results
        children_stats = self.helper.get_children_stats(person_set.id)
        results["childrenStats"] = {
            "M": children_stats.male,
            "F": children_stats.female,
            "U": children_stats.unspecified
        }
        results["selector"] = person_set.name
        results["geneSymbols"] = list(self.gene_syms)
        results["peopleGroupId"] = self.person_set_collection.id
        results["peopleGroupValue"] = person_set.id
        results["datasetId"] = self.dataset.study_id

        return results

    def _build_results(self) -> list[dict[str, Any]]:
        results = []

        effect_types = self.enrichment_config["effect_types"]

        for person_set in self.person_set_collection.person_sets.values():
            res = self.build_people_group_selector(effect_types, person_set)
            if res:
                results.append(res)

        return results

    def build(self) -> list[dict[str, Any]]:
        results = self._build_results()

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
        gene_syms: Iterable[str]
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
            self.client.post_enrichment_test(self.query)["result"]
        )
