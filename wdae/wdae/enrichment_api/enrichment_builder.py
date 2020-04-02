from dae.enrichment_tool.genotype_helper import GenotypeHelper


class EnrichmentBuilder(object):
    def __init__(self, dataset, enrichment_tool, gene_syms):
        self.dataset = dataset
        self.gene_syms = gene_syms
        self.tool = enrichment_tool
        self.results = None

    def build_people_group_selector(
        self, effect_types, person_set_collection, person_set_id
    ):

        gh = GenotypeHelper(self.dataset, person_set_collection, person_set_id)

        children_stats = gh.get_children_stats()
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
                gh.get_variants(effect_type),
                gh.children_by_sex(),
            )

            results[effect_type] = enrichment_results
        results["childrenStats"] = gh.get_children_stats()
        results["selector"] = person_set_id
        results["geneSymbols"] = list(self.gene_syms)
        results["peopleGroupId"] = person_set_collection.id
        results["peopleGroupValue"] = person_set_id
        results["datasetId"] = self.dataset.id

        return results

    def build(self):
        results = []
        enrichment_config = self.tool.config
        assert enrichment_config is not None

        effect_types = enrichment_config.effect_types

        # TODO Why is only one person set collection being used here?
        person_set_collection = self.dataset.get_person_set_collection(
            enrichment_config.selected_person_set_collections[0]
        )

        for person_set_id in person_set_collection.person_sets:
            res = self.build_people_group_selector(
                effect_types, person_set_collection, person_set_id
            )
            if res:
                results.append(res)

        self.results = results
        return self.results
