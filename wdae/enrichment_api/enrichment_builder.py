'''
Created on Feb 17, 2017

@author: lubo
'''
from enrichment_tool.tool import EnrichmentTool
from enrichment_tool.event_counters import EnrichmentResult


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

    def in_child(self, phenotype):
        if phenotype == 'unaffected':
            return 'sib'
        else:
            return 'prb'

    def build_phenotype(self, phenotype):
        results = {}
        studies = self.dataset.denovo_studies
        studies = [
            st for st in studies
            if phenotype == st.get_attr('study.phenotype')
        ]
        for effect_type in self.EFFECT_TYPES:
            enrichment_results = self.tool.calc(
                studies,
                self.in_child(phenotype),
                effect_type,
                self.gene_syms,
                self.dataset.children_stats[phenotype])

            results[effect_type] = enrichment_results

        return results

    def build(self):
        results = {}
        for phenotype in self.dataset.get_phenotypes():
            res = self.build_phenotype(phenotype)
            results[phenotype] = res
        self.result = results
        return self.result

    def serialize_enrichment_result(self, result):
        assert isinstance(result, EnrichmentResult)
        res = {}
        res['name'] = result.name
        res['count'] = len(result.events)
        res['overlapped'] = len(result.overlapped)
        res['expected'] = result.expected
        res['pvalue'] = result.pvalue
        return res

    def serialize_helper(self, result):
        print(type(result))
        if isinstance(result, EnrichmentResult):
            return self.serialize_enrichment_result(result)
        else:
            return dict([
                (k, self.serialize_helper(v)) for k, v in result.items()
            ])

    def serialize(self):
        assert self.result is not None
        return self.serialize_helper(self.result)
