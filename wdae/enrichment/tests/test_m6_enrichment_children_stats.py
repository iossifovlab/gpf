'''
Created on Jun 22, 2015

@author: lubo
'''
import unittest
from DAE import vDB
from enrichment.families import ChildrenStats
from helpers.logger import LOGGER


class Test(unittest.TestCase):

    def setUp(self):
        self.dsts = vDB.get_studies('ALL WHOLE EXOME')

    def tearDown(self):
        pass

    def test_children_stats_simple(self):
        stats = ChildrenStats.build(self.dsts)

        LOGGER.info('enrichment children stats: {}'.format(stats))
        self.assertEquals(596, stats['autism']['F'])
        self.assertEquals(3367, stats['autism']['M'])

        self.assertEquals(1192, stats['unaffected']['F'])
        self.assertEquals(1111, stats['unaffected']['M'])


if __name__ == "__main__":
    unittest.main()
