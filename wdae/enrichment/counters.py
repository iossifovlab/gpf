'''
Created on Sep 29, 2016

@author: lubo
'''
import itertools

from DAE import vDB
from enrichment.config import PHENOTYPES, EnrichmentConfig
from enrichment.denovo_counters import filter_denovo_one_event_per_family,\
    filter_denovo_one_gene_per_recurrent_events,\
    filter_denovo_one_gene_per_events


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


class CounterBase(EnrichmentConfig):

    def __init__(self, phenotype, effect_type):
        super(CounterBase, self).__init__(phenotype, effect_type)

    def get_variants(self, denovo_studies):
        studies = denovo_studies.get_studies(self.phenotype)
        variants = []
        for st in studies:
            vs = st.get_denovo_variants(
                inChild=self.in_child, effectTypes=self.effect_type)
            variants.append(vs)
        return list(itertools.chain(*variants))

    def events(self, denovo_studies):
        raise NotImplementedError()

#     def overlapped_events(self, denovo_studies, gene_set):
#         events = self.events(denovo_studies)
#         return self.overlap_events(events, gene_set)
#
#     def full_events(self, denovo_studies, gene_set):
#         events = self.events(denovo_studies)
#         overlapped_events = self.overlap_events(events, gene_set)
#
#         return events, overlapped_events


class EventsResult(EnrichmentConfig):

    def __init__(self, config):
        super(EventsResult, self).__init__(
            config.phenotype, config.effect_type)

    def __call__(self, events, rec_events, boys_events, girls_events):
        self.all_events = events
        self.rec_events = rec_events
        self.male_events = boys_events
        self.female_events = girls_events

        self.all_count = len(self.all_events)
        self.rec_count = len(self.rec_events)
        self.male_count = len(self.male_events)
        self.female_count = len(self.female_events)

        return self

    @staticmethod
    def filter_overlapping_events(events, gene_set):
        gene_syms = [gs.upper() for gs in gene_set]
        return [ev for ev in events if any([gs in gene_syms for gs in ev])]

    def overlap(self, gene_set):
        all_events = self.filter_overlapping_events(
            self.all_events, gene_set)
        rec_events = self.filter_overlapping_events(
            self.rec_events, gene_set)
        male_events = self.filter_overlapping_events(
            self.male_events, gene_set)
        female_events = self.filter_overlapping_events(
            self.female_events, gene_set)
        return EventsResult(self)(
            all_events, rec_events, male_events, female_events)


class EventsCounter(CounterBase):

    def __init__(self, phenotype, effect_type):
        super(EventsCounter, self).__init__(phenotype, effect_type)

    def events(self, denovo_studies):
        variants = self.get_variants(denovo_studies)
        male_variants = [v for v in variants if v.inChS[3] == 'M']
        female_variants = [v for v in variants if v.inChS[3] == 'F']

        all_events = filter_denovo_one_event_per_family(variants)
        rec_events = filter_denovo_one_gene_per_recurrent_events(variants)
        male_events = filter_denovo_one_event_per_family(male_variants)
        female_events = filter_denovo_one_event_per_family(female_variants)

        return EventsResult(self)(
            all_events, rec_events, male_events, female_events)


class GeneEventsCounter(CounterBase):

    def __init__(self, phenotype, effect_type):
        super(GeneEventsCounter, self).__init__(phenotype, effect_type)

    def events(self, denovo_studies):
        variants = self.get_variants(denovo_studies)
        male_variants = [v for v in variants if v.inChS[3] == 'M']
        female_variants = [v for v in variants if v.inChS[3] == 'F']

        all_events = filter_denovo_one_gene_per_events(variants)
        rec_events = filter_denovo_one_gene_per_recurrent_events(variants)
        male_events = filter_denovo_one_gene_per_events(male_variants)
        female_events = filter_denovo_one_gene_per_events(female_variants)

        return EventsResult(self)(
            all_events, rec_events, male_events, female_events)
