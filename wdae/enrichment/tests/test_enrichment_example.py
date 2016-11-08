'''
Created on Oct 4, 2016

@author: lubo
'''

import unittest
from DAE import get_gene_sets_symNS
import precompute
from enrichment_tool.config import DenovoStudies, ChildrenStats
from enrichment_tool.event_counters import GeneEventsCounter


class EnrichmentExampleTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(EnrichmentExampleTest, cls).setUpClass()
        cls.denovo_studies = DenovoStudies()
        gt = get_gene_sets_symNS('main')
        cls.gene_set = gt.t2G['ChromatinModifiers'].keys()

        cls.children_stats = ChildrenStats.build(cls.denovo_studies)

    def test_samocha_model(self):
        background = precompute.register.get('samochaBackgroundModel')

        counter = GeneEventsCounter('autism', 'LGDs')
        events = counter.events(self.denovo_studies)

        stats = background.calc_stats(
            events, self.gene_set,
            self.children_stats['autism'])

        self.assertIsNotNone(stats)
