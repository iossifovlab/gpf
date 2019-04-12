'''
Created on Feb 17, 2017

@author: lubo
'''
from __future__ import unicode_literals
from builtins import object
from enrichment_tool.tool import EnrichmentTool
from enrichment_tool.genotype_helper import GenotypeHelper as GH


class EnrichmentBuilder(object):
    EFFECT_TYPES = [
        'LGDs',
        'missense',
        'synonymous'
    ]

    def __init__(self, dataset, enrichment_model, gene_syms):
        self.dataset = dataset
        self.enrichment_model = enrichment_model
        self.gene_syms = gene_syms
        self.tool = EnrichmentTool(
            self.enrichment_model['background'],
            self.enrichment_model['counting']
        )
        self.results = None

    def build_person_grouping_selector(
            self, person_grouping, person_grouping_selector):

        gh = GH.from_dataset(
            self.dataset,
            person_grouping,
            person_grouping_selector)

        children_stats = gh.get_children_stats()
        children_count = children_stats['M'] + \
            children_stats['F'] + children_stats['U']

        if children_count <= 0:
            return None

        results = {}
        for effect_type in self.EFFECT_TYPES:
            enrichment_results = self.tool.calc(
                effect_type,
                self.gene_syms,
                gh.get_variants(effect_type),
                gh.get_children_stats())

            results[effect_type] = enrichment_results
        results['childrenStats'] = gh.get_children_stats()
        # results['selector'] = person_grouping_selector
        results['geneSymbols'] = list(self.gene_syms)
        results['personGroupingId'] = person_grouping
        results['personGroupingValue'] = person_grouping_selector
        results['datasetId'] = self.dataset.dataset_id
        return results

    def build(self):
        results = []
        enrichment_config = self.dataset.descriptor.get('enrichmentTool')
        assert enrichment_config is not None
        person_grouping_id = enrichment_config['selector']
        person_grouping = self.dataset.get_pedigree_selector(
            default=False,
            person_grouping=person_grouping_id)

        for person_grouping_selector in person_grouping.domain:
            res = self.build_person_grouping_selector(
                person_grouping_id,
                person_grouping_selector['id'])
            if res:
                res['personGroupingValue'] = person_grouping_selector['id']
                res['selector'] = person_grouping_selector['name']
                results.append(res)
        self.results = results
        return self.results

#     def serialize_enrichment_result(self, result):
#         assert isinstance(result, EnrichmentResult)
#         res = {}
#         res['name'] = result.name
#         res['count'] = len(result.events)
#         res['overlapped'] = len(result.overlapped)
#         res['expected'] = result.expected
#         res['pvalue'] = result.pvalue
#         return res
#
#     def serialize_helper(self, result):
#         if isinstance(result, EnrichmentResult):
#             return self.serialize_enrichment_result(result)
#         elif isinstance(result, list):
#             return [
#                 self.serialize_helper(v) for v in result
#             ]
#         elif isinstance(result, str) or isinstance(result, int) or \
#                 isinstance(result, float):
#             return result
#         else:
#             return dict([
#                 (k, self.serialize_helper(v)) for k, v in result.items()
#             ])
#
#     def serialize(self):
#         assert self.results is not None
#         return self.serialize_helper(self.results)
