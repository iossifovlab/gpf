'''
Created on Oct 22, 2015

@author: lubo
'''
import unittest

from Variant import present_in_parent_filter


class PresentInParentFilterTest(unittest.TestCase):

    def test_father_only(self):
        f = present_in_parent_filter(
            ['father only'])
        self.assertTrue(f('dad'))
        self.assertFalse(f('mom'))
        self.assertFalse(f('momdad'))
        self.assertFalse(f(''))

    def test_mother_only(self):
        f = present_in_parent_filter(
            ['mother only'])
        self.assertTrue(f('mom'))
        self.assertFalse(f('dad'))
        self.assertFalse(f('momdad'))
        self.assertFalse(f(''))

    def test_mother_only_and_father_only(self):
        f = present_in_parent_filter(
            ['mother only', 'father only'])
        self.assertTrue(f('mom'))
        self.assertTrue(f('dad'))
        self.assertFalse(f('momdad'))
        self.assertFalse(f(''))

    def test_mother_and_father(self):
        f = present_in_parent_filter(
            ['mother and father'])
        self.assertFalse(f('mom'))
        self.assertFalse(f('dad'))
        self.assertTrue(f('momdad'))
        self.assertFalse(f(''))

    def test_mother_only_and_mother_and_father(self):
        f = present_in_parent_filter(
            ['mother only', 'mother and father'])
        self.assertTrue(f('mom'))
        self.assertFalse(f('dad'))
        self.assertTrue(f('momdad'))
        self.assertFalse(f(''))

    def test_father_only_and_mother_and_father(self):
        f = present_in_parent_filter(
            ['father only', 'mother and father'])
        self.assertFalse(f('mom'))
        self.assertTrue(f('dad'))
        self.assertTrue(f('momdad'))
        self.assertFalse(f(''))

    def test_father_only_and_mother_only_and_mother_and_father(self):
        f = present_in_parent_filter(
            ['father only', 'mother only', 'mother and father'])
        self.assertTrue(f('mom'))
        self.assertTrue(f('dad'))
        self.assertTrue(f('momdad'))
        self.assertFalse(f(''))

    def test_neither(self):
        f = present_in_parent_filter(
            ['neither'])
        self.assertFalse(f('dad'))
        self.assertFalse(f('mom'))
        self.assertFalse(f('momdad'))
        self.assertTrue(f(''))

    def test_all(self):
        f = present_in_parent_filter(
            ['father only', 'mother only', 'mother and father', 'neither'])
        self.assertIsNone(f)

#         self.assertTrue(f('mom'))
#         self.assertTrue(f('dad'))
#         self.assertTrue(f('momdad'))
#         self.assertTrue(f(''))

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
