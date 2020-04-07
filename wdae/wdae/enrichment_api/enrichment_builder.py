from dae.enrichment_tool.genotype_helper import GenotypeHelper
from dae.utils.effect_utils import expand_effect_types


class EnrichmentBuilder(object):
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

    def build_people_group_selector(
            self, effect_types, person_set_id):

        children_stats = self.gh.get_children_stats(person_set_id)
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
                self.gh.children_by_sex(person_set_id),
            )

            results[effect_type] = enrichment_results
        results["childrenStats"] = self.gh.get_children_stats(person_set_id)
        results["selector"] = person_set_id
        results["geneSymbols"] = list(self.gene_syms)
        results["peopleGroupId"] = self.person_set_collection.id
        results["peopleGroupValue"] = person_set_id
        results["datasetId"] = self.dataset.id

        return results

    def build(self):
        results = []
        enrichment_config = self.tool.config
        assert enrichment_config is not None

        effect_types = enrichment_config.effect_types

        for person_set_id in self.person_set_collection.person_sets:
            res = self.build_people_group_selector(
                effect_types, person_set_id)
            if res:
                results.append(res)

        self.results = results
        return self.results
