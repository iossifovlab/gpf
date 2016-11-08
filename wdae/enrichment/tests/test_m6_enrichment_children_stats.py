'''
Created on Jun 22, 2015

@author: lubo
'''
import unittest
from helpers.logger import LOGGER
from enrichment_tool.config import DenovoStudies, ChildrenStats


class Test(unittest.TestCase):

    def setUp(self):
        self.denovo_studies = DenovoStudies()

    def tearDown(self):
        pass

    def test_children_stats_simple(self):
        stats = ChildrenStats.build(self.denovo_studies)

        LOGGER.info('enrichment children stats: {}'.format(stats))
        self.assertEquals(596, stats['autism']['F'])
        self.assertEquals(3367, stats['autism']['M'])

        self.assertEquals(1111, stats['unaffected']['M'])
        self.assertEquals(1192, stats['unaffected']['F'])
