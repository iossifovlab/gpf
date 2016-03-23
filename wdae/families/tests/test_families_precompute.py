'''
Created on Feb 29, 2016

@author: lubo
'''
import unittest
from families.families_precompute import FamiliesPrecompute


class Test(unittest.TestCase):

    def test_families_gender_precompute(self):
        fgender = FamiliesPrecompute()
        fgender.precompute()

        self.assertIsNotNone(fgender._siblings)
        self.assertIsNotNone(fgender._probands)

    def test_families_gender_serialize_deserialize(self):
        fgender = FamiliesPrecompute()
        fgender.precompute()

        data = fgender.serialize()

        fg = FamiliesPrecompute()
        fg.deserialize(data)

        self.assertEqual(fgender._probands, fg._probands)
        self.assertEqual(fgender._siblings, fg._siblings)

    def test_families_trios_quads_precompute(self):
        fgender = FamiliesPrecompute()
        fgender.precompute()

        self.assertIsNotNone(fgender._trios)
        self.assertIsNotNone(fgender._quads)

    def test_families_trios_quads_serialize_deserialize(self):
        fgender = FamiliesPrecompute()
        fgender.precompute()

        data = fgender.serialize()

        fg = FamiliesPrecompute()
        fg.deserialize(data)

        self.assertEqual(fgender._trios, fg._trios)
        self.assertEqual(fgender._quads, fg._quads)

    def test_families_races_precompute(self):
        fgender = FamiliesPrecompute()
        fgender.precompute()

        self.assertIsNotNone(fgender._races)

    def test_families_races_serialize_deserialize(self):
        fgender = FamiliesPrecompute()
        fgender.precompute()

        data = fgender.serialize()

        fg = FamiliesPrecompute()
        fg.deserialize(data)

        self.assertEqual(fgender._races, fg._races)

    def test_families_buffer_precompute(self):
        fgender = FamiliesPrecompute()
        fgender.precompute()

        self.assertIsNotNone(fgender._families_buffer)
