'''
Created on Feb 17, 2017

@author: lubo
'''
from __future__ import unicode_literals
from builtins import object

from enrichment_tool.genotype_helper import GenotypeHelper


class EnrichmentBuilder(object):

    def __init__(self, dataset, enrichment_tool, gene_syms):
        self.dataset = dataset
        self.gene_syms = gene_syms
        self.tool = enrichment_tool
        self.results = None

    def build_people_group_selector(
            self, effect_types, people_group, people_group_value):

        gh = GenotypeHelper(
            self.dataset,
            people_group,
            people_group_value)

        children_stats = gh.get_children_stats()
        children_count = children_stats['M'] + \
            children_stats['F'] + children_stats['U']

        if children_count <= 0:
            return None

        results = {}
        for effect_type in effect_types:
            enrichment_results = self.tool.calc(
                effect_type,
                self.gene_syms,
                gh.get_variants(effect_type),
                gh.get_children_stats())

            results[effect_type] = enrichment_results
        results['childrenStats'] = gh.get_children_stats()
        results['selector'] = people_group_value
        results['geneSymbols'] = list(self.gene_syms)
        results['peopleGroupId'] = people_group.id
        results['peopleGroupValue'] = people_group_value
        results['datasetId'] = self.dataset.id

        return results

    def build(self):
        results = []
        enrichment_config = self.tool.config
        assert enrichment_config is not None

        effect_types = enrichment_config.effect_types

        people_group_id = enrichment_config.people_groups[0]
        people_group = self.dataset.config.people_group_config.\
            get_people_group(people_group_id)

        for people_group_selector in people_group.domain:
            res = self.build_people_group_selector(
                effect_types,
                people_group,
                people_group_selector['name'])
            if res:
                results.append(res)
        self.results = results
        return self.results
