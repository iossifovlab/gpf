'''
Created on Sep 29, 2016

@author: lubo
'''
from enrichment.config import PHENOTYPES, EnrichmentConfig
from DAE import vDB
import itertools
from enrichment.denovo_counters import filter_denovo_one_event_per_family,\
    filter_denovo_one_gene_per_recurrent_events, count_denovo_variant_events


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

    def __init__(self, phenotype, effect_types):
        super(CounterBase, self).__init__(phenotype, effect_types)
        if phenotype == 'unaffected':
            self.in_child = 'sib'
        else:
            self.in_child = 'prb'

    def count(self, denovo_studies, gene_set):
        raise NotImplementedError()

    def get_variants(self, denovo_studies):
        studies = denovo_studies.get_studies(self.phenotype)
        variants = []
        for st in studies:
            vs = st.get_denovo_variants(
                inChild=self.in_child, effectTypes=self.effect_types)
            variants.append(vs)
        return list(itertools.chain(*variants))

    def filter_events(self, denovo_studies):
        pass


class EventsResult(object):

    def __init__(self, events, rec_events, boys_events, girls_events):
        self.total_events = events
        self.rec_events = rec_events
        self.male_events = boys_events
        self.female_events = girls_events


class EventsCounter(CounterBase):

    def __init__(self, phenotype, effect_types):
        super(EventsCounter, self).__init__(phenotype, effect_types)

    def enrichment_events(self, denovo_studies, gene_set):
        events = self.filter_events(denovo_studies)

        total_events = count_denovo_variant_events(
            events.total_events, gene_set)
        rec_events = count_denovo_variant_events(
            events.rec_events, gene_set)
        male_events = count_denovo_variant_events(
            events.male_events, gene_set)
        female_events = count_denovo_variant_events(
            events.female_events, gene_set)

        return EventsResult(
            total_events, rec_events, male_events, female_events)

    def filter_events(self, denovo_studies):
        variants = self.get_variants(denovo_studies)
        male_variants = [v for v in variants if v.inChS[3] == 'M']
        female_variants = [v for v in variants if v.inChS[3] == 'F']

        total_events = filter_denovo_one_event_per_family(variants)
        rec_events = filter_denovo_one_gene_per_recurrent_events(variants)
        male_events = filter_denovo_one_event_per_family(male_variants)
        female_events = filter_denovo_one_event_per_family(female_variants)

        return EventsResult(
            total_events, rec_events, male_events, female_events)
