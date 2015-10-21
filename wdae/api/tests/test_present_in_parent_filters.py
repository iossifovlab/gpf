import unittest
import logging
import urllib
import itertools

LOGGER = logging.getLogger(__name__)

from query_variants import prepare_present_in_parent

class PresentInParentTests(unittest.TestCase):

    def test_father_only(self):
        f = prepare_present_in_parent(
            {'presentInParent':'father only'})
        self.assertTrue(f('dad'))
        self.assertFalse(f('mom'))
        self.assertFalse(f('momdad'))
        self.assertFalse(f(''))

    def test_mother_only(self):
        f = prepare_present_in_parent(
            {'presentInParent':'mother only'})
        self.assertTrue(f('mom'))
        self.assertFalse(f('dad'))
        self.assertFalse(f('momdad'))
        self.assertFalse(f(''))

    def test_mother_only_and_father_only(self):
        f = prepare_present_in_parent(
            {'presentInParent':'mother only,father only'})
        self.assertTrue(f('mom'))
        self.assertTrue(f('dad'))
        self.assertFalse(f('momdad'))
        self.assertFalse(f(''))
        
    def test_mother_and_father(self):
        f = prepare_present_in_parent(
            {'presentInParent':'mother and father'})
        self.assertFalse(f('mom'))
        self.assertFalse(f('dad'))
        self.assertTrue(f('momdad'))
        self.assertFalse(f(''))

    def test_mother_only_and_mother_and_father(self):
        f = prepare_present_in_parent(
            {'presentInParent':'mother only,mother and father'})
        self.assertTrue(f('mom'))
        self.assertFalse(f('dad'))
        self.assertTrue(f('momdad'))
        self.assertFalse(f(''))

    def test_father_only_and_mother_and_father(self):
        f = prepare_present_in_parent(
            {'presentInParent':'father only,mother and father'})
        self.assertFalse(f('mom'))
        self.assertTrue(f('dad'))
        self.assertTrue(f('momdad'))
        self.assertFalse(f(''))

    def test_father_only_and_mother_only_and_mother_and_father(self):
        f = prepare_present_in_parent(
            {'presentInParent':'father only,mother only,mother and father'})
        self.assertTrue(f('mom'))
        self.assertTrue(f('dad'))
        self.assertTrue(f('momdad'))
        self.assertFalse(f(''))

    def test_neither(self):
        f = prepare_present_in_parent(
            {'presentInParent':'neither'})
        self.assertFalse(f('dad'))
        self.assertFalse(f('mom'))
        self.assertFalse(f('momdad'))
        self.assertTrue(f(''))

    def test_all(self):
        f = prepare_present_in_parent(
            {'presentInParent':'father only,mother only,mother and father,neither'})
        self.assertTrue(f('mom'))
        self.assertTrue(f('dad'))
        self.assertTrue(f('momdad'))
        self.assertTrue(f(''))
