'''
Created on Sep 30, 2016

@author: lubo
'''
import unittest

from enrichment.counters import DenovoStudies, EventsCounter
from DAE import get_gene_sets_symNS


class EventsCounterTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(EventsCounterTest, cls).setUpClass()
        cls.denovo_studies = DenovoStudies()
        gt = get_gene_sets_symNS('main')
        cls.gene_set = gt.t2G['ChromatinModifiers'].keys()

    def test_events_autism_with_effect_type_lgd(self):
        counter = EventsCounter('autism', 'LGDs')

        events = counter.all_events(self.denovo_studies)

        self.assertIsNotNone(events)

        self.assertEquals(606, len(events.total_events))
        self.assertEquals(39, len(events.rec_events))
        self.assertEquals(492, len(events.male_events))
        self.assertEquals(114, len(events.female_events))

    def test_events_unaffected_with_effect_type_lgd(self):
        counter = EventsCounter('unaffected', 'LGDs')

        events = counter.all_events(self.denovo_studies)

        self.assertIsNotNone(events)

        self.assertEquals(224, len(events.total_events))
        self.assertEquals(5, len(events.rec_events))
        self.assertEquals(113, len(events.male_events))
        self.assertEquals(111, len(events.female_events))

    def test_events_schizophrenia_with_effect_type_lgd(self):
        counter = EventsCounter('schizophrenia', 'LGDs')

        events = counter.all_events(self.denovo_studies)

        self.assertIsNotNone(events)
        self.assertEquals(95, len(events.total_events))
        self.assertEquals(2, len(events.rec_events))

        self.assertEquals(49, len(events.male_events))
        self.assertEquals(46, len(events.female_events))

        print(events.rec_events)
        print(events.female_events)

    def test_overlapped_events_autism_with_effect_type_lgd(self):
        counter = EventsCounter('autism', 'LGDs')

        events = counter.overlapped_events(
            self.denovo_studies, self.gene_set)

        self.assertIsNotNone(events)

        self.assertEquals(56, len(events.total_events))
        self.assertEquals(9, len(events.rec_events))
        self.assertEquals(40, len(events.male_events))
        self.assertEquals(16, len(events.female_events))

    def test_overlapped_events_unaffected_with_effect_type_synonymous(self):
        counter = EventsCounter('unaffected', 'synonymous')

        events = counter.overlapped_events(
            self.denovo_studies, self.gene_set)

        self.assertIsNotNone(events)

        self.assertEquals(18, len(events.total_events))
        self.assertEquals(1, len(events.rec_events))
        self.assertEquals(14, len(events.male_events))
        self.assertEquals(4, len(events.female_events))

    def test_overlapped_events_schizophrenia_with_effect_type_missense(self):
        counter = EventsCounter('schizophrenia', 'missense')

        events = counter.overlapped_events(
            self.denovo_studies, self.gene_set)

        self.assertIsNotNone(events)

        self.assertEquals(23, len(events.total_events))
        self.assertEquals(2, len(events.rec_events))
        self.assertEquals(10, len(events.male_events))
        self.assertEquals(13, len(events.female_events))
