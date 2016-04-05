'''
Created on Apr 1, 2016

@author: lubo
'''
import unittest

import precompute
from DAE import vDB
import itertools
from pprint import pprint


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
        for st in itertools.chain(studies):
            for fid, family in st.families.items():

                if fid not in quads:
                    continue
                if(4 != len(family.memberInOrder)):
                    print(
                        "quad family not always quad: {}; study: {}".format(
                            fid, st.name))
                    pprint(family.memberInOrder)

    def test_11000_is_quad(self):
        quads = self.families_precompute.quads()
        self.assertNotIn('11000', quads)
