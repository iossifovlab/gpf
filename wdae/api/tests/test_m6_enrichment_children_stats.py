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
        self.assertEquals(593, stats['autism']['F'])
        self.assertEquals(3360, stats['autism']['M'])
        
        self.assertEquals(1058, stats['unaffected']['F'])
        self.assertEquals(971, stats['unaffected']['M'])


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()