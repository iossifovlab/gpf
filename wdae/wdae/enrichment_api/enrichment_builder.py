from .enrichment_serializer import EnrichmentSerializer

from dae.enrichment_tool.genotype_helper import GenotypeHelper
from dae.utils.effect_utils import expand_effect_types


class BaseEnrichmentBuilder:
    def build(self):
        raise NotImplementedError()


class EnrichmentBuilder(BaseEnrichmentBuilder):
    def __init__(
            self, dataset, enrichment_tool, gene_syms):
        self.dataset = dataset
        self.gene_syms = gene_syms
        self.tool = enrichment_tool
        self.results = None
        enrichment_config = self.tool.config
        assert enrichment_config is not None
        effect_types = expand_effect_types(enrichment_config.effect_types)

        self.person_set_collection = self.dataset.get_person_set_collection(
            enrichment_config.selected_person_set_collections[0]
        )

        self.gh = GenotypeHelper(
            self.dataset, self.person_set_collection,
            effect_types=effect_types)

    def build_people_group_selector(self, effect_types, person_set):
        children_stats = self.gh.get_children_stats(person_set.id)
        children_count = (
            children_stats["M"] + children_stats["F"] + children_stats["U"]
        )

        if children_count <= 0:
            return None

        results = {}
        for effect_type in effect_types:
            enrichment_results = self.tool.calc(
                effect_type,
                self.gene_syms,
                self.gh.get_denovo_variants(),
                self.gh.children_by_sex(person_set.id),
            )

            results[effect_type] = enrichment_results
        results["childrenStats"] = self.gh.get_children_stats(person_set.id)
        results["selector"] = person_set.name
        results["geneSymbols"] = list(self.gene_syms)
        results["peopleGroupId"] = self.person_set_collection.id
        results["peopleGroupValue"] = person_set.id
        results["datasetId"] = self.dataset.study_id

        return results

    def _build_results(self):
        results = []
        enrichment_config = self.tool.config
        assert enrichment_config is not None

        effect_types = enrichment_config.effect_types

        for person_set in self.person_set_collection.person_sets.values():
            res = self.build_people_group_selector(effect_types, person_set)
            if res:
                results.append(res)

        return results

    def build(self):
        results = self._build_results()

        serializer = EnrichmentSerializer(self.tool.config, results)
        results = serializer.serialize()

        self.results = results
        return self.results


class RemoteEnrichmentBuilder(BaseEnrichmentBuilder):

    def __init__(
            self, dataset, client, background_name, counting_name, gene_syms):
        self.dataset = dataset
        self.client = client
        query = dict()
        query["datasetId"] = dataset._remote_study_id
        query["geneSymbols"] = list(gene_syms)
        query["enrichmentBackgroundModel"] = background_name
        query["enrichmentCountingModel"] = counting_name
        self.query = query

    def build(self):
        return self.client.post_enrichment_test(self.query)["result"]
