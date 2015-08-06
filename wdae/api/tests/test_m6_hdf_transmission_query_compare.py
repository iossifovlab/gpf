'''
Created on Aug 6, 2015

@author: lubo
'''
import unittest
from api.variants.hdf5_query import TransmissionQuery
from DAE import vDB


def dae_summary_by_gene_syms(gene_syms):
    transmitted_study = vDB.get_study("w1202s766e611")
    vs = transmitted_study.get_transmitted_summary_variants(
        geneSyms=gene_syms)
    res = [v for v in vs]
    return res


def dae_summary_by_effect_types(effect_types):
    transmitted_study = vDB.get_study("w1202s766e611")
    vs = transmitted_study.get_transmitted_summary_variants(
        effectTypes=effect_types)
    res = [v for v in vs]
    return res


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass()
        cls.tquery = TransmissionQuery('w1202s766e611')

    def setUp(self):
        pass

    def tearDown(self):
        self.tquery.clear_query()

    def test_hdf_execute_effect_query_2_gene_syms(self):
        tq = self.tquery
        tq['gene_syms'] = ['POGZ', 'SCNN1D']
        vs = tq.execute_effect_query()
        self.assertIsNotNone(vs)
        self.assertEquals(333, len(vs))
        res = dae_summary_by_gene_syms(["POGZ", "SCNN1D"])
        self.assertEqual(len(res), len(vs))

    def test_hdf_execute_effect_query_1_gene_syms(self):
        tq = self.tquery
        tq['gene_syms'] = ['POGZ']
        vs = tq.execute_effect_query()
        self.assertIsNotNone(vs)
        res = dae_summary_by_gene_syms(["POGZ"])
        self.assertEqual(len(res), len(vs))

    def test_hdf_effect_type_query_lgds(self):
        lgds = ['nonsense', 'frame-shift', 'splice-site']
        tq = self.tquery
        tq['effect_types'] = lgds
        vs = tq.execute_effect_query()
        self.assertIsNotNone(vs)

        res = dae_summary_by_effect_types(lgds)
        self.assertEquals(len(res), len(vs))

    def test_hdf_effect_query_combined(self):
        tq = self.tquery
        tq['gene_syms'] = ['POGZ', 'SCNN1D']
        tq['effect_types'] = ['nonsense', 'frame-shift', 'splice-site']
        tq['variant_types'] = ['ins', 'sub']
        vs = tq.execute_effect_query()
        self.assertIsNotNone(vs)
        self.assertEquals(2, len(vs))

        transmitted_study = vDB.get_study("w1202s766e611")
        tvs = transmitted_study.get_transmitted_summary_variants(
            effectTypes=['nonsense', 'frame-shift', 'splice-site'],
            geneSyms=['POGZ', 'SCNN1D'],
            variantTypes=['ins', 'sub'])
        res = [v for v in tvs]
        self.assertEquals(len(res), len(vs))


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
