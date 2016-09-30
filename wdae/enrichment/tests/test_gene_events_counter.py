'''
Created on Sep 30, 2016

@author: lubo
'''
import unittest

from enrichment.counters import DenovoStudies, GeneEventsCounter
from DAE import get_gene_sets_symNS


class EventsCounterTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(EventsCounterTest, cls).setUpClass()
        cls.denovo_studies = DenovoStudies()
        gt = get_gene_sets_symNS('main')
        cls.gene_set = gt.t2G['ChromatinModifiers'].keys()

    def test_events_autism_with_effect_type_lgd(self):
        counter = GeneEventsCounter('autism', 'LGDs')

        events = counter.events(self.denovo_studies)

        self.assertIsNotNone(events)

        self.assertEquals(546, len(events.all_events))
        self.assertEquals(39, len(events.rec_events))
        self.assertEquals(458, len(events.male_events))
        self.assertEquals(107, len(events.female_events))

    def test_events_unaffected_with_effect_type_lgd(self):
        counter = GeneEventsCounter('unaffected', 'LGDs')

        events = counter.events(self.denovo_studies)

        self.assertIsNotNone(events)

        self.assertEquals(220, len(events.all_events))
        self.assertEquals(5, len(events.rec_events))
        self.assertEquals(113, len(events.male_events))
        self.assertEquals(111, len(events.female_events))

    def test_events_schizophrenia_with_effect_type_lgd(self):
        counter = GeneEventsCounter('schizophrenia', 'LGDs')

        events = counter.events(self.denovo_studies)

        self.assertIsNotNone(events)
        self.assertEquals(93, len(events.all_events))
        self.assertEquals(2, len(events.rec_events))

        self.assertEquals(48, len(events.male_events))
        self.assertEquals(45, len(events.female_events))

        print(events.rec_events)
        print(events.female_events)

    def test_overlapped_events_autism_with_effect_type_lgd(self):
        counter = GeneEventsCounter('autism', 'LGDs')

        events = counter.overlapped_events(
            self.denovo_studies, self.gene_set)

        self.assertIsNotNone(events)

        self.assertEquals(36, len(events.all_events))
        self.assertEquals(9, len(events.rec_events))
        self.assertEquals(28, len(events.male_events))
        self.assertEquals(13, len(events.female_events))

    def test_overlapped_events_unaffected_with_effect_type_synonymous(self):
        counter = GeneEventsCounter('unaffected', 'synonymous')

        events = counter.overlapped_events(
            self.denovo_studies, self.gene_set)

        self.assertIsNotNone(events)

        self.assertEquals(17, len(events.all_events))
        self.assertEquals(1, len(events.rec_events))
        self.assertEquals(13, len(events.male_events))
        self.assertEquals(4, len(events.female_events))

    def test_overlapped_events_schizophrenia_with_effect_type_missense(self):
        counter = GeneEventsCounter('schizophrenia', 'missense')

        events = counter.overlapped_events(
            self.denovo_studies, self.gene_set)

        self.assertIsNotNone(events)

        self.assertEquals(21, len(events.all_events))
        self.assertEquals(2, len(events.rec_events))
        self.assertEquals(9, len(events.male_events))
        self.assertEquals(12, len(events.female_events))
