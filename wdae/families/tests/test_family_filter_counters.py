'''
Created on Mar 23, 2016

@author: lubo
'''
import unittest
import precompute
from families.counters import FamilyFilterCounters


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass()
        families_precompute = precompute.register.get('families_precompute')
        cls.families_buffer = families_precompute.families_buffer()

    def test_has_family_buffer(self):
        self.assertIsNotNone(self.families_buffer)

    def test_empty_families(self):
        counter = FamilyFilterCounters(self.families_buffer)
        result = counter.count([])

        self.assertIn('autism', result)
        self.assertIn('unaffected', result)

        prb = result['autism']
        self.assertEquals(0, prb['male'])
        self.assertEquals(0, prb['female'])
        self.assertEquals(0, prb['families'])

        sib = result['unaffected']
        self.assertEquals(0, sib['male'])
        self.assertEquals(0, sib['female'])
        self.assertEquals(0, sib['families'])

    def test_single_family_11008(self):
        counter = FamilyFilterCounters(self.families_buffer)
        result = counter.count(['11008'])

        prb = result['autism']
        self.assertEquals(1, prb['male'])
        self.assertEquals(0, prb['female'])
        self.assertEquals(1, prb['families'])

        sib = result['unaffected']
        self.assertEquals(1, sib['male'])
        self.assertEquals(0, sib['female'])
        self.assertEquals(1, sib['families'])

    def test_single_family_11114(self):
        counter = FamilyFilterCounters(self.families_buffer)
        result = counter.count(['11114'])

        prb = result['autism']
        self.assertEquals(0, prb['male'])
        self.assertEquals(1, prb['female'])
        self.assertEquals(1, prb['families'])

        sib = result['unaffected']
        self.assertEquals(0, sib['male'])
        self.assertEquals(1, sib['female'])
        self.assertEquals(1, sib['families'])

    def test_two_families_11008_and_11114(self):
        counter = FamilyFilterCounters(self.families_buffer)
        result = counter.count(['11008', '11114'])

        prb = result['autism']
        self.assertEquals(1, prb['male'])
        self.assertEquals(1, prb['female'])
        self.assertEquals(2, prb['families'])

        sib = result['unaffected']
        self.assertEquals(1, sib['male'])
        self.assertEquals(1, sib['female'])
        self.assertEquals(2, sib['families'])
