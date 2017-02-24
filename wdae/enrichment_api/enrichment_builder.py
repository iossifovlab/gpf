'''
Created on Feb 17, 2017

@author: lubo
'''
from common.query_base import EffectTypesMixin
import itertools
from enrichment_tool.tool import EnrichmentTool


class EnrichmentConfig(EffectTypesMixin):

    def __init__(self, phenotype, effect_type):
        self.phenotype = phenotype

        et = self.build_effect_types(effect_type)
        # assert 1 == len(et)

        self.effect_type = ','.join(et)

        if phenotype == 'unaffected':
            self.in_child = 'sib'
        else:
            self.in_child = 'prb'


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

    def in_child(self, phenotype):
        if phenotype == 'unaffected':
            return 'sib'
        else:
            return 'prb'

    def build_phenotype(self, phenotype):
        results = []
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

            row = RowResult(phenotype, effect_type)(enrichment_results)
            results.append(row)

        res = PhenotypeResult(phenotype)(results)
        return res

    def build(self):
        results = EnrichmentResult()

        for phenotype in self.dataset.get_phenotypes():
            res = self.build_phenotype(phenotype)
            results(res)
        self.result = results
        return self.result


class CellResult(EnrichmentConfig):

    @staticmethod
    def filter_effect_type(effect_type):
        if 'lgds' == effect_type.lower():
            return 'Nonsense,Frame-shift,Splice-site'
        elif 'missense' == effect_type.lower():
            return 'Missense'
        elif 'synonymous' == effect_type.lower():
            return 'Synonymous'

    @staticmethod
    def name_effect_type(effect_type):
        if 'lgds' == effect_type.lower():
            return 'LGDs'
        elif 'missense' == effect_type.lower():
            return 'Missense'
        elif 'synonymous' == effect_type.lower():
            return 'Synonymous'
        return effect_type

    @staticmethod
    def _interpolate_gender(gender):
        if gender is None:
            return 'male,female'
        if gender == 'M':
            return 'male'
        if gender == 'F':
            return 'female'
        raise ValueError("unexpected gender: {}".format(gender))

    def __init__(self, phenotype, effect_type, gender=None, rec=False):
        super(CellResult, self).__init__(phenotype, effect_type)
        self.gender = self._interpolate_gender(gender)
        self.rec = rec

    def __call__(self, result):
        self.events = result.events
        self.overlapped_events = result.overlapped

        self.count = len(self.events)
        self.overlapped_count = len(self.overlapped_events)

        self.expected = result.expected
        self.pvalue = result.pvalue
        return self

    def serialize(self):
        res = {}
        res['name'] = self.name
        res['effectType'] = self.effect_type
        res['gender'] = self.gender
        res['count'] = self.count
        res['overlapped_count'] = self.overlapped_count
        res['expected'] = self.expected
        res['pvalue'] = self.pvalue
        return res

    def __repr__(self):
        return "ER({}; " \
            "count: {}, overlapped: {}, expected: {}, pvalue: {})".format(
                self.name,
                self.count,
                self.overlapped_count,
                self.expected,
                self.pvalue
            )

    @property
    def filter(self):
        return [
            self.in_child,
            self.gender,
            self.filter_effect_type(self.effect_type)
        ]

    @property
    def name(self):
        if self.rec:
            return "Rec {}".format(self.name_effect_type(self.effect_type))
        else:
            et = self.name_effect_type(self.effect_type)
            if self.gender == 'male':
                return 'Male {}'.format(et)
            if self.gender == 'female':
                return 'Female {}'.format(et)
            return et

    @property
    def overlapped_gene_syms(self):
        return list(set(itertools.chain.from_iterable(self.overlapped_events)))

    @property
    def gene_syms(self):
        return list(set(itertools.chain.from_iterable(self.events)))


class RowResult(EnrichmentConfig):
    TESTS = ['all', 'rec', 'male', 'female']

    def __init__(self, phenotype, effect_type):
        super(RowResult, self).__init__(phenotype, effect_type)

    def __call__(self, enrichment_results):
        self.results = {}

        self.results['all'] = CellResult(
            self.phenotype, self.effect_type)(
                enrichment_results['all'])
        self.results['rec'] = CellResult(
            self.phenotype, self.effect_type, rec=True)(
                enrichment_results['rec'])
        self.results['male'] = CellResult(
            self.phenotype, self.effect_type, gender='M')(
                enrichment_results['male'])
        self.results['female'] = CellResult(
            self.phenotype, self.effect_type, gender='F')(
                enrichment_results['female'])
        return self

    def __repr__(self):
        return "{}".format(self.results)

    def __getitem__(self, test):
        return self.results[test]

    def __contains__(self, test):
        return test in self.results

    def __getattr__(self, test):
        if test not in self.results:
            raise AttributeError("unexpected test: {}".format(test))
        return self.results[test]

    def serialize(self):
        res = dict([(k, v.serialize()) for (k, v) in self.results.items()])
        return res


class PhenotypeResult(object):

    def __init__(self, phenotype):
        self.phenotype = phenotype
        self._result = {}

    def __call__(self, results):
        for r in results:
            self._result[r.effect_type.lower()] = r
        return self

    def __repr__(self):
        return "{}".format(self._result)

    def __getattr__(self, effect_type):
        et = effect_type.lower()
        if et not in self._result:
            raise AttributeError("bad effect type: {}".format(effect_type))
        return self._result[et]

    def __getitem__(self, effect_type):
        et = effect_type.lower()
        if et not in self._result:
            raise KeyError("bad effect type: {}".format(effect_type))
        return self._result[et]

    def __contains__(self, effect_type):
        return effect_type.lower() in self._result

    def serialize(self):
        res = {}
        res['phenotype'] = self.phenotype
        res['results'] = [r.serialize() for r in self._result.values()]
        return res


class EnrichmentResult(object):

    def __init__(self):
        self.results = {}

    def __call__(self, phenotype_result):
        self.results[phenotype_result.phenotype] = phenotype_result

    def serialize(self):
        res = dict([(k, v.serialize()) for k, v in self.results.items()])
        return res
