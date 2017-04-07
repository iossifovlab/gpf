'''
Created on Sep 30, 2016

@author: lubo
'''
import itertools

from DAE import vDB
from VariantAnnotation import get_effect_types
from enrichment_tool.tool import EnrichmentTool
from query_prepare import build_effect_types_list
from enrichment_tool.config import children_stats_counter


PHENOTYPES = [
    'autism',
    'congenital heart disease',
    'epilepsy',
    'intellectual disability',
    'schizophrenia',
    'unaffected',
]

EFFECT_TYPES = [
    'LGDs',
    'missense',
    'synonymous'
]


class DenovoStudies(object):

    def __init__(self):
        self.studies = vDB.get_studies('ALL WHOLE EXOME')

    def get_studies(self, phenotype):
        assert phenotype in PHENOTYPES
        if phenotype == 'unaffected':
            studies = [st for st in self.studies
                       if 'WE' == st.get_attr('study.type')]
            return studies
        else:
            studies = []
            for st in self.studies:
                if phenotype == st.get_attr('study.phenotype') and \
                        'WE' == st.get_attr('study.type'):
                    studies.append(st)
            return studies


class EnrichmentConfig(object):
    EFFECT_TYPES = get_effect_types(True, True)

    def __init__(self, phenotype, effect_type):
        assert phenotype in PHENOTYPES
        self.phenotype = phenotype

        et = build_effect_types_list([effect_type])
        assert 1 == len(et)
        assert all([e in self.EFFECT_TYPES for e in et])

        self.effect_type = ','.join(et)

        if phenotype == 'unaffected':
            self.in_child = 'sib'
        else:
            self.in_child = 'prb'


class ChildrenStats(object):

    @staticmethod
    def build(denovo_studies):
        res = {}
        for phenotype in PHENOTYPES:
            studies = denovo_studies.get_studies(phenotype)
            if phenotype == 'unaffected':
                stats = children_stats_counter(studies, 'sib')
            else:
                stats = children_stats_counter(studies, 'prb')
            res[phenotype] = stats
        return res


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

    def __getitem__(self, test):
        return self.results[test]

    def __contains__(self, test):
        return test in self.results

    def __getattr__(self, test):
        if test not in self.results:
            raise AttributeError("unexpected test: {}".format(test))
        return self.results[test]


class PhenotypeResult(object):

    def __init__(self, phenotype):
        self.phenotype = phenotype
        self._result = {}

    def __call__(self, results):
        for r in results:
            self._result[r.effect_type.lower()] = r
        return self

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


class EnrichmentResult(object):

    def __init__(self, results):
        self.results = results

    def __getitem__(self, phenotype):
        return self.results[phenotype]

    def __contains__(self, phenotype):
        return phenotype in self.results


class EnrichmentBuilder(object):

    def __init__(
            self, background, denovo_counter,
            denovo_studies, children_stats,
            gene_set):

        self.tool = EnrichmentTool(background, denovo_counter)
        self.gene_set = gene_set
        self.children_stats = children_stats
        self.denovo_studies = denovo_studies

    def in_child(self, phenotype):
        if phenotype == 'unaffected':
            return 'sib'
        else:
            return 'prb'

    def build_phenotype(self, phenotype):
        results = []
        for effect_type in EFFECT_TYPES:
            enrichment_results = self.tool.calc(
                    self.denovo_studies.get_studies(phenotype),
                    self.in_child(phenotype),
                    effect_type,
                    self.gene_set,
                    self.children_stats[phenotype])

            row = RowResult(phenotype, effect_type)(enrichment_results)
            results.append(row)

        res = PhenotypeResult(phenotype)(results)
        return res

    def build(self):
        results = {}

        for phenotype in PHENOTYPES:
            res = self.build_phenotype(phenotype)
            results[phenotype] = res
        self.result = EnrichmentResult(results)
        return self.result
