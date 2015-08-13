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


def dae_query_by_family_ids(family_ids):
    transmitted_study = vDB.get_study("w1202s766e611")
    tvs = transmitted_study.get_transmitted_variants(
        familyIds=family_ids)
    res = [v for v in tvs]
    return res


def dae_summary_by_regions(regions):
    transmitted_study = vDB.get_study("w1202s766e611")
    tvs = transmitted_study.get_transmitted_summary_variants(
        regionS=regions)
    res = [v for v in tvs]
    return res


def dae_lgds_in_prb():
    transmitted_study = vDB.get_study("w1202s766e611")
    tvs = transmitted_study.get_transmitted_variants(
        effectTypes=['nonsense', 'frame-shift', 'splice-site'],
        inChild='prb')

    res = [v for v in tvs]
    return res


def dae_ultra_rare_lgds_in_prb():
    transmitted_study = vDB.get_study("w1202s766e611")
    tvs = transmitted_study.get_transmitted_variants(
        effectTypes=['nonsense', 'frame-shift', 'splice-site'],
        ultraRareOnly=True,
        inChild='prb')

    res = [v for v in tvs]
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

    def test_hdf_family_query_family_ids(self):
        tq = self.tquery
        tq['family_ids'] = ['14474', '14346']
        vs = tq.execute_family_query()
        self.assertIsNotNone(vs)
        self.assertEquals(57839, len(vs))

        transmitted_study = vDB.get_study("w1202s766e611")
        tvs = transmitted_study.get_transmitted_variants(
            familyIds=['14474', '14346'],
            minParentsCalled=-1,
            maxAltFreqPrcnt=-1,
            minAltFreqPrcnt=-1,
            effectTypes=None
            )
        res = [v for v in tvs]
        self.assertEquals(len(res), len(vs))

    def test_hdf_regions_search(self):
        tq = self.tquery
        tq['regions'] = ["12:76770000-76890000"]
        vs = tq.execute_summary_variants_query()
        self.assertIsNotNone(vs)
        self.assertEquals(70, len(vs))

        transmitted_study = vDB.get_study("w1202s766e611")
        tvs = transmitted_study.get_transmitted_summary_variants(
            regionS=["12:76770000-76890000"])
        res = [v for v in tvs]
        self.assertEquals(len(res), len(vs))

    def test_hdf_prb_lgds(self):
        tq = self.tquery
        tq['effect_types'] = ['nonsense', 'frame-shift', 'splice-site']
        tq['present_in_child'] = ['prb']
        vs = tq.get_variants()
        self.assertIsNotNone(vs)
        self.assertEquals(71596, len(vs))

#         transmitted_study = vDB.get_study("w1202s766e611")
#         tvs = transmitted_study.get_transmitted_variants(
#             effectTypes=['nonsense', 'frame-shift', 'splice-site'],
#             inChild='prb')
#
#         res = [v for v in tvs]
#         self.assertEquals(71596, len(res))

    def test_hdf_ultra_rare_lgds_in_prb(self):
        tq = self.tquery
        tq['effect_types'] = ['nonsense', 'frame-shift', 'splice-site']
        tq['present_in_child'] = ['prb']
        tq['ultra_rare_only'] = True
        vs = tq.get_variants()
        self.assertIsNotNone(vs)
        self.assertEquals(14401, len(vs))

#         transmitted_study = vDB.get_study("w1202s766e611")
#         tvs = transmitted_study.get_transmitted_variants(
#             effectTypes=['nonsense', 'frame-shift', 'splice-site'],
#             ultraRareOnly=True,
#             inChild='prb')
#
#         res = [v for v in tvs]
#         self.assertEquals(14401, len(res))

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
