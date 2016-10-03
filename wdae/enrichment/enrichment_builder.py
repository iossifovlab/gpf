'''
Created on Sep 30, 2016

@author: lubo
'''
from enrichment.config import EnrichmentConfig, EFFECT_TYPES, PHENOTYPES
import itertools


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

    def __init__(self, config, gender=None, rec=False):
        super(CellResult, self).__init__(config.phenotype, config.effect_type)
        self.gender = self._interpolate_gender(gender)
        self.rec = rec

    def __call__(self, events, overlapped_events, expected, pvalue):
        self.events = events
        self.overlapped_events = overlapped_events

        self.count = len(self.events)
        self.overlapped_count = len(self.overlapped_events)

        self.expected = expected
        self.pvalue = pvalue
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
        return set(itertools.chain.from_iterable(self.overlapped_events))

    @property
    def gene_syms(self):
        return set(itertools.chain.from_iterable(self.events))


class RowResult(EnrichmentConfig):
    TESTS = ['all', 'rec', 'male', 'female']

    def __init__(self, config):
        super(RowResult, self).__init__(config.phenotype, config.effect_type)

    def __call__(self, events, overlapped_events, enrichment_stats):
        self.results = {}

        self.results['all'] = CellResult(events)(
            events.all_events,
            overlapped_events.all_events,
            enrichment_stats.all_expected,
            enrichment_stats.all_pvalue)
        self.results['rec'] = CellResult(events, rec=True)(
            events.rec_events,
            overlapped_events.rec_events,
            enrichment_stats.rec_expected,
            enrichment_stats.rec_pvalue)
        self.results['male'] = CellResult(events, gender='M')(
            events.male_events,
            overlapped_events.male_events,
            enrichment_stats.male_expected,
            enrichment_stats.male_pvalue)
        self.results['female'] = CellResult(events, gender='F')(
            events.female_events,
            overlapped_events.female_events,
            enrichment_stats.female_expected,
            enrichment_stats.female_pvalue)

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
            denovo_studies, gene_set, children_stats):
        self.background = background
        self.denovo_counter = denovo_counter
        self.denovo_studies = denovo_studies
        self.gene_set = gene_set
        self.children_stats = children_stats

    def events_by_phenotype_and_effect_type(
            self, phenotype, effect_type):
        counter = self.denovo_counter(
            phenotype, effect_type)
        events, overlapped_events = counter.full_events(
            self.denovo_studies, self.gene_set)

        stats = self.background.calc_stats(
            events, overlapped_events, self.gene_set,
            self.children_stats[phenotype])
        return events, overlapped_events, stats

    def build_phenotype(self, phenotype):
        results = []
        for effect_type in EFFECT_TYPES:
            events, overlapped_events, enrichment_stats = \
                self.events_by_phenotype_and_effect_type(
                    phenotype, effect_type)
            row = RowResult(events)(
                events, overlapped_events, enrichment_stats)
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
