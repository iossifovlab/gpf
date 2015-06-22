'''
Created on Jun 22, 2015

@author: lubo
'''
import unittest
from DAE import vDB
from api.enrichment.families import ChildrenStats
from api.logger import LOGGER


class Test(unittest.TestCase):


    def setUp(self):
        self.dsts = vDB.get_studies('ALL WHOLE EXOME') 


    def tearDown(self):
        pass


    def test_children_stats_simple(self):
        stats = ChildrenStats.build(self.dsts)
        
        LOGGER.info('enrichment children stats: {}'.format(stats))
        self.assertEquals(3953, stats['autism']['prb'])
        self.assertEquals(1911, stats['autism']['sib'])
        
        self.assertEquals(5694, stats['unaffected']['prb'])
        self.assertEquals(2029, stats['unaffected']['sib'])


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()