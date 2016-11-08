'''
Created on Jun 9, 2015

@author: lubo
'''
import unittest
import numpy as np
from DAE import vDB
from enrichment_tool.background import SynonymousBackground


class SynonymousBackgroundTest(unittest.TestCase):

    def test_synonymous_background(self):
        synbg = SynonymousBackground()
        bg = synbg.precompute()
        self.assertEquals(211645, np.sum(bg['raw']))
#         self.assertAlmostEqual(1.0, np.sum(bg['weight']), 5)

    def test_synonymous_summary_variants(self):
        st = vDB.get_study("w1202s766e611")
        ovs = st.get_transmitted_summary_variants(
                ultraRareOnly=True,
                minParentsCalled=600,
                effectTypes=["synonymous"],
                callSet='old')
        mvs = st.get_transmitted_summary_variants(
                ultraRareOnly=True,
                minParentsCalled=600,
                effectTypes=["synonymous"])
        ores = [v for v in ovs]
        mres = [v for v in mvs]
        self.assertEquals(len(ores), len(mres))

    def test_affected_gene_syms(self):
        self.maxDiff = None
        st = vDB.get_study("w1202s766e611")
        ovs = st.get_transmitted_summary_variants(
                ultraRareOnly=True,
                minParentsCalled=600,
                effectTypes=["synonymous"],
                callSet='old')
        mvs = st.get_transmitted_summary_variants(
                ultraRareOnly=True,
                minParentsCalled=600,
                effectTypes=["synonymous"])

        oaffected = SynonymousBackground._collect_affected_gene_syms(ovs)
        maffected = SynonymousBackground._collect_affected_gene_syms(mvs)
        self.assertEquals(oaffected, maffected)
