'''
Created on Jun 9, 2015

@author: lubo
'''
import unittest
from DAE import vDB, get_gene_sets_symNS
from api.enrichment.denovo_counters import collect_denovo_variants,\
    filter_denovo_one_event_per_family

class Test(unittest.TestCase):


    def setUp(self):
        self.dsts = vDB.get_studies('ALL WHOLE EXOME')
        gt = get_gene_sets_symNS('main')
        self.gene_syms = gt.t2G['FMR1-targets-1006genes'].keys()

    def tearDown(self):
        pass


    def test_collect_denovo_variants(self):
        vs = collect_denovo_variants(self.dsts, self.gene_syms,
                                     'autism',
                                     ('prb|LGDs|prb|LGD', 'prb', 'LGDs'))
        res = filter_denovo_one_event_per_family(vs)
        print(res)
        self.assertEquals(137, len(res))

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_collect_denovo_variants']
    unittest.main()