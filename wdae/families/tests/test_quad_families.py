'''
Created on Apr 1, 2016

@author: lubo
'''
import unittest

import precompute
from DAE import vDB
import itertools


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass()
        cls.families_precompute = precompute.register.get(
            'families_precompute')
        cls.families_buffer = cls.families_precompute.families_buffer()

    def test_quad_families(self):
        quads = self.families_precompute.quads()
        self.assertIsNotNone(quads)

        studies = vDB.get_studies('ALL SSC')
        seen = set()
        for st in itertools.chain(studies):
            for fid, family in st.families.items():
                if fid in seen:
                    continue
                seen.add(fid)

                if fid not in quads:
                    continue
                self.assertEquals(4, len(family.memberInOrder))

    def test_11000_is_quad(self):
        quads = self.families_precompute.quads()
        self.assertIn('11000', quads)
