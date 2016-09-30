'''
Created on Sep 30, 2016

@author: lubo
'''
from enrichment.config import EnrichmentConfig, EFFECT_TYPES


class CellResult(EnrichmentConfig):

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
        self.pvale = pvalue
        return self

    @property
    def filter(self):
        return '{}|{}|{}'.format(self.in_child, self.gender, self.name)

    @property
    def name(self):
        if self.rec:
            return "Rec {}".format(self.effect_type)
        else:
            return self.effect_type


class RowResult(EnrichmentConfig):

    def __init__(self, config):
        super(RowResult, self).__init__(config.phenotype, config.effect_type)

    def __call__(self, events, overlapped_events, enrichment_stats):
        self.all_result = CellResult(events)(
            events.all_events,
            overlapped_events.all_events,
            enrichment_stats.all_expected,
            enrichment_stats.all_pvalue)
        self.rec_result = CellResult(events, rec=True)(
            events.rec_events,
            overlapped_events.rec_events,
            enrichment_stats.rec_expected,
            enrichment_stats.rec_pvalue)
        self.male_result = CellResult(events, gender='M')(
            events.male_events,
            overlapped_events.male_events,
            enrichment_stats.male_expected,
            enrichment_stats.male_pvalue)
        self.female_result = CellResult(events, gender='F')(
            events.female_events,
            overlapped_events.female_events,
            enrichment_stats.female_expected,
            enrichment_stats.female_pvalue)

        return self

    @property
    def all(self):
        return self.all_result

    @property
    def rec(self):
        return self.rec_result

    @property
    def male(self):
        return self.male_result

    @property
    def female(self):
        return self.female_result


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


class EnrichmentBuilder(object):

    def __init__(self, background, denovo_counter, denovo_studies, gene_set):
        self.background = background
        self.denovo_counter = denovo_counter
        self.denovo_studies = denovo_studies
        self.gene_set = gene_set

    def events_by_phenotype_and_effect_type(self, phenotype, effect_type):
        counter = self.denovo_counter(
            phenotype, effect_type)
        events, overlapped_events = counter.full_events(
            self.denovo_studies, self.gene_set)
        stats = self.background.calc_stats(
            events, overlapped_events, self.gene_set)
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
