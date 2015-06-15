import unittest
import logging
import urllib
import itertools

LOGGER = logging.getLogger(__name__)

from query_variants import prepare_present_in_child
from query_prepare import prepare_gender_filter

class PresentInChildTests(unittest.TestCase):
    # denovo SSC
    # {'prbM': 2933,
    #  'sibF': 1227,
    #  'sibM': 1037,
    #  'prbF': 529,
    #  'prbMsibM': 20,
    #  'prbMsibF': 19,
    #  'prbFsibF': 2,
    #  'prbFsibM': 2,
    #  '': 1,
    #  'dad': 1,
    #  'mom': 1}

    # transmitted SSC
    # {'': 3098926,
    #  'prbM': 2973499,
    #  'prbMsibF': 1094578,
    #  'sibF': 1060837,
    #  'prbMsibM': 943168,
    #  'sibM': 915439,
    #  'prbF': 506979,
    #  'prbFsibF': 162977,
    #  'prbFsibM': 148217}
    
    def test_autism_only(self):
        f = prepare_present_in_child(
            {'presentInChild':'autism only'})
        self.assertTrue(f('prbF'))
        self.assertTrue(f('prbM'))
        self.assertFalse(f('sibF'))
        self.assertFalse(f('sibM'))
        self.assertFalse(f('prbMsibM'))
        self.assertFalse(f('prbMsibF'))
        self.assertFalse(f('prbFsibM'))
        self.assertFalse(f('prbFsibF'))
        self.assertFalse(f(''))

    def test_unaffected_only(self):
        f = prepare_present_in_child(
            {'presentInChild':'unaffected only'})
        self.assertFalse(f('prbF'))
        self.assertFalse(f('prbM'))
        self.assertTrue(f('sibF'))
        self.assertTrue(f('sibM'))
        self.assertFalse(f('prbMsibM'))
        self.assertFalse(f('prbMsibF'))
        self.assertFalse(f('prbFsibM'))
        self.assertFalse(f('prbFsibF'))
        self.assertFalse(f(''))

    def test_autism_and_unaffected(self):
        f = prepare_present_in_child(
            {'presentInChild':'autism and unaffected'})
        self.assertFalse(f('prbF'))
        self.assertFalse(f('prbM'))
        self.assertFalse(f('sibF'))
        self.assertFalse(f('sibM'))
        self.assertTrue(f('prbMsibM'))
        self.assertTrue(f('prbMsibF'))
        self.assertTrue(f('prbFsibM'))
        self.assertTrue(f('prbFsibF'))
        self.assertFalse(f(''))

    def test_neither(self):
        f = prepare_present_in_child(
            {'presentInChild':'neither'})
        self.assertFalse(f('prbF'))
        self.assertFalse(f('prbM'))
        self.assertFalse(f('sibF'))
        self.assertFalse(f('sibM'))
        self.assertFalse(f('prbMsibM'))
        self.assertFalse(f('prbMsibF'))
        self.assertFalse(f('prbFsibM'))
        self.assertFalse(f('prbFsibF'))
        self.assertTrue(f(''))

    def test_autism_only_and_unaffected_only(self):
        f = prepare_present_in_child(
            {'presentInChild':'autism only,unaffected only'})
        self.assertTrue(f('prbF'))
        self.assertTrue(f('prbM'))
        self.assertTrue(f('sibF'))
        self.assertTrue(f('sibM'))
        self.assertFalse(f('prbMsibM'))
        self.assertFalse(f('prbMsibF'))
        self.assertFalse(f('prbFsibM'))
        self.assertFalse(f('prbFsibF'))
        self.assertFalse(f(''))

    def test_autism_only_and_unaffected_only_and_autism_and_unaffected(self):
        f = prepare_present_in_child(
            {'presentInChild':'autism only,unaffected only,autism and unaffected'})
        self.assertTrue(f('prbF'))
        self.assertTrue(f('prbM'))
        self.assertTrue(f('sibF'))
        self.assertTrue(f('sibM'))
        self.assertTrue(f('prbMsibM'))
        self.assertTrue(f('prbMsibF'))
        self.assertTrue(f('prbFsibM'))
        self.assertTrue(f('prbFsibF'))
        self.assertFalse(f(''))

    def test_autism_only_and_unaffected_only_and_autism_and_unaffected_neigher(self):
        f = prepare_present_in_child(
            {'presentInChild':'autism only,unaffected only,autism and unaffected,neither'})
        self.assertTrue(f('prbF'))
        self.assertTrue(f('prbM'))
        self.assertTrue(f('sibF'))
        self.assertTrue(f('sibM'))
        self.assertTrue(f('prbMsibM'))
        self.assertTrue(f('prbMsibF'))
        self.assertTrue(f('prbFsibM'))
        self.assertTrue(f('prbFsibF'))
        self.assertTrue(f(''))

    def test_autism_only_gender_male(self):
        data = {
            'presentInChild':'autism only',
            'gender': 'male'
        }
        prepare_gender_filter(data)
        print data
        
        f = prepare_present_in_child(data)
        
        self.assertFalse(f('prbF'))
        self.assertTrue(f('prbM'))
        self.assertFalse(f('sibF'))
        self.assertFalse(f('sibM'))
        self.assertFalse(f('prbMsibM'))
        self.assertFalse(f('prbMsibF'))
        self.assertFalse(f('prbFsibM'))
        self.assertFalse(f('prbFsibF'))
        self.assertFalse(f(''))

    def test_autism_only_gender_female(self):
        data = {
            'presentInChild':'autism only',
            'gender': 'female'
        }
        prepare_gender_filter(data)
        print data
        
        f = prepare_present_in_child(data)
        
        self.assertTrue(f('prbF'))
        self.assertFalse(f('prbM'))
        self.assertFalse(f('sibF'))
        self.assertFalse(f('sibM'))
        self.assertFalse(f('prbMsibM'))
        self.assertFalse(f('prbMsibF'))
        self.assertFalse(f('prbFsibM'))
        self.assertFalse(f('prbFsibF'))
        self.assertFalse(f(''))


    def test_autism_only_gender_male_and_female(self):
        data = {
            'presentInChild':'autism only',
            'gender': 'male,female'
        }
        prepare_gender_filter(data)
        print data
        
        f = prepare_present_in_child(data)
        
        self.assertTrue(f('prbF'))
        self.assertTrue(f('prbM'))
        self.assertFalse(f('sibF'))
        self.assertFalse(f('sibM'))
        self.assertFalse(f('prbMsibM'))
        self.assertFalse(f('prbMsibF'))
        self.assertFalse(f('prbFsibM'))
        self.assertFalse(f('prbFsibF'))
        self.assertFalse(f(''))

    def test_unaffected_only_gender_male(self):
        data = {
            'presentInChild':'unaffected only',
            'gender': 'male'
        }
        prepare_gender_filter(data)
        print data
        
        f = prepare_present_in_child(data)

        self.assertFalse(f('prbF'))
        self.assertFalse(f('prbM'))
        self.assertFalse(f('sibF'))
        self.assertTrue(f('sibM'))
        self.assertFalse(f('prbMsibM'))
        self.assertFalse(f('prbMsibF'))
        self.assertFalse(f('prbFsibM'))
        self.assertFalse(f('prbFsibF'))
        self.assertFalse(f(''))

    def test_unaffected_only_gender_female(self):
        data = {
            'presentInChild':'unaffected only',
            'gender': 'female'
        }
        prepare_gender_filter(data)
        print data
        
        f = prepare_present_in_child(data)

        self.assertFalse(f('prbF'))
        self.assertFalse(f('prbM'))
        self.assertTrue(f('sibF'))
        self.assertFalse(f('sibM'))
        self.assertFalse(f('prbMsibM'))
        self.assertFalse(f('prbMsibF'))
        self.assertFalse(f('prbFsibM'))
        self.assertFalse(f('prbFsibF'))
        self.assertFalse(f(''))

    def test_unaffected_only_gender_male_and_female(self):
        data = {
            'presentInChild':'unaffected only',
            'gender': 'male,female'
        }
        prepare_gender_filter(data)
        print data
        
        f = prepare_present_in_child(data)

        self.assertFalse(f('prbF'))
        self.assertFalse(f('prbM'))
        self.assertTrue(f('sibF'))
        self.assertTrue(f('sibM'))
        self.assertFalse(f('prbMsibM'))
        self.assertFalse(f('prbMsibF'))
        self.assertFalse(f('prbFsibM'))
        self.assertFalse(f('prbFsibF'))
        self.assertFalse(f(''))
        
    def test_autism_and_unaffected_gender_male(self):
        data = {
            'presentInChild':'autism and unaffected',
            'gender': 'male'
        }
        prepare_gender_filter(data)
        print data
        
        f = prepare_present_in_child(data)

        self.assertFalse(f('prbF'))
        self.assertFalse(f('prbM'))
        self.assertFalse(f('sibF'))
        self.assertFalse(f('sibM'))
        self.assertTrue(f('prbMsibM'))
        self.assertTrue(f('prbMsibF'))
        self.assertFalse(f('prbFsibM'))
        self.assertFalse(f('prbFsibF'))
        self.assertFalse(f(''))

    def test_autism_and_unaffected_gender_female(self):
        data = {
            'presentInChild':'autism and unaffected',
            'gender': 'female'
        }
        prepare_gender_filter(data)
        print data
        
        f = prepare_present_in_child(data)

        self.assertFalse(f('prbF'))
        self.assertFalse(f('prbM'))
        self.assertFalse(f('sibF'))
        self.assertFalse(f('sibM'))
        self.assertFalse(f('prbMsibM'))
        self.assertFalse(f('prbMsibF'))
        self.assertTrue(f('prbFsibM'))
        self.assertTrue(f('prbFsibF'))
        self.assertFalse(f(''))

    def test_autism_and_unaffected_gender_male_and_female(self):
        data = {
            'presentInChild':'autism and unaffected',
            'gender': 'female'
        }
        prepare_gender_filter(data)
        print data
        
        f = prepare_present_in_child(data)

        self.assertFalse(f('prbF'))
        self.assertFalse(f('prbM'))
        self.assertFalse(f('sibF'))
        self.assertFalse(f('sibM'))
        self.assertFalse(f('prbMsibM'))
        self.assertFalse(f('prbMsibF'))
        self.assertTrue(f('prbFsibM'))
        self.assertTrue(f('prbFsibF'))
        self.assertFalse(f(''))

    def test_neither_gender_male(self):
        data = {
            'presentInChild':'neither',
            'gender': 'male'
        }
        prepare_gender_filter(data)
        print data
        
        f = prepare_present_in_child(data)

        self.assertFalse(f('prbF'))
        self.assertFalse(f('prbM'))
        self.assertFalse(f('sibF'))
        self.assertFalse(f('sibM'))
        self.assertFalse(f('prbMsibM'))
        self.assertFalse(f('prbMsibF'))
        self.assertFalse(f('prbFsibM'))
        self.assertFalse(f('prbFsibF'))
        self.assertTrue(f(''))

    def test_neither_gender_female(self):
        data = {
            'presentInChild':'neither',
            'gender': 'female'
        }
        prepare_gender_filter(data)
        print data
        
        f = prepare_present_in_child(data)

        self.assertFalse(f('prbF'))
        self.assertFalse(f('prbM'))
        self.assertFalse(f('sibF'))
        self.assertFalse(f('sibM'))
        self.assertFalse(f('prbMsibM'))
        self.assertFalse(f('prbMsibF'))
        self.assertFalse(f('prbFsibM'))
        self.assertFalse(f('prbFsibF'))
        self.assertTrue(f(''))

        
    def test_neither_gender_male_and_female(self):
        data = {
            'presentInChild':'neither',
            'gender': 'male,female'
        }
        prepare_gender_filter(data)
        print data
        
        f = prepare_present_in_child(data)

        self.assertFalse(f('prbF'))
        self.assertFalse(f('prbM'))
        self.assertFalse(f('sibF'))
        self.assertFalse(f('sibM'))
        self.assertFalse(f('prbMsibM'))
        self.assertFalse(f('prbMsibF'))
        self.assertFalse(f('prbFsibM'))
        self.assertFalse(f('prbFsibF'))
        self.assertTrue(f(''))

    def test_autism_only_and_unaffected_only_gender_male(self):
        data = {
            'presentInChild':'autism only,unaffected only',
            'gender': 'male'
        }
        prepare_gender_filter(data)
        print data
        
        f = prepare_present_in_child(data)

        self.assertFalse(f('prbF'))
        self.assertTrue(f('prbM'))
        self.assertFalse(f('sibF'))
        self.assertTrue(f('sibM'))
        self.assertFalse(f('prbMsibM'))
        self.assertFalse(f('prbMsibF'))
        self.assertFalse(f('prbFsibM'))
        self.assertFalse(f('prbFsibF'))
        self.assertFalse(f(''))

    def test_autism_only_and_unaffected_only_gender_female(self):
        data = {
            'presentInChild':'autism only,unaffected only',
            'gender': 'female'
        }
        prepare_gender_filter(data)
        print data
        
        f = prepare_present_in_child(data)

        self.assertTrue(f('prbF'))
        self.assertFalse(f('prbM'))
        self.assertTrue(f('sibF'))
        self.assertFalse(f('sibM'))
        self.assertFalse(f('prbMsibM'))
        self.assertFalse(f('prbMsibF'))
        self.assertFalse(f('prbFsibM'))
        self.assertFalse(f('prbFsibF'))
        self.assertFalse(f(''))

    def test_autism_only_and_unaffected_only_gender_male_and_female(self):
        data = {
            'presentInChild':'autism only,unaffected only',
            'gender': 'male,female'
        }
        prepare_gender_filter(data)
        print data
        
        f = prepare_present_in_child(data)

        self.assertTrue(f('prbF'))
        self.assertTrue(f('prbM'))
        self.assertTrue(f('sibF'))
        self.assertTrue(f('sibM'))
        self.assertFalse(f('prbMsibM'))
        self.assertFalse(f('prbMsibF'))
        self.assertFalse(f('prbFsibM'))
        self.assertFalse(f('prbFsibF'))
        self.assertFalse(f(''))

    def test_autism_only_and_unaffected_only_and_autism_and_uaffected_gender_male(self):
        data = {
            'presentInChild':'autism only,unaffected only,autism and unaffected',
            'gender': 'male',
        }
        prepare_gender_filter(data)
        print data
        
        f = prepare_present_in_child(data)

        self.assertFalse(f('prbF'))
        self.assertTrue(f('prbM'))
        self.assertFalse(f('sibF'))
        self.assertTrue(f('sibM'))
        self.assertTrue(f('prbMsibM'))
        self.assertTrue(f('prbMsibF'))
        self.assertFalse(f('prbFsibM'))
        self.assertFalse(f('prbFsibF'))
        self.assertFalse(f(''))

    def test_autism_only_and_unaffected_only_and_autism_and_uaffected_gender_female(self):
        data = {
            'presentInChild':'autism only,unaffected only,autism and unaffected',
            'gender': 'female',
        }
        prepare_gender_filter(data)
        print data
        
        f = prepare_present_in_child(data)

        self.assertTrue(f('prbF'))
        self.assertFalse(f('prbM'))
        self.assertTrue(f('sibF'))
        self.assertFalse(f('sibM'))
        self.assertFalse(f('prbMsibM'))
        self.assertFalse(f('prbMsibF'))
        self.assertTrue(f('prbFsibM'))
        self.assertTrue(f('prbFsibF'))
        self.assertFalse(f(''))


    def test_autism_only_and_unaffected_only_and_autism_and_uaffected_gender_male_and_female(self):
        data = {
            'presentInChild':'autism only,unaffected only,autism and unaffected',
            'gender': 'male,female',
        }
        prepare_gender_filter(data)
        print data
        
        f = prepare_present_in_child(data)

        self.assertTrue(f('prbF'))
        self.assertTrue(f('prbM'))
        self.assertTrue(f('sibF'))
        self.assertTrue(f('sibM'))
        self.assertTrue(f('prbMsibM'))
        self.assertTrue(f('prbMsibF'))
        self.assertTrue(f('prbFsibM'))
        self.assertTrue(f('prbFsibF'))
        self.assertFalse(f(''))

    def test_autism_only_and_unaffected_only_and_autism_and_unaffected_neither_gender_male(self):
        data = {
            'presentInChild':'autism only,unaffected only,autism and unaffected,neither',
            'gender': 'male',
        }
        prepare_gender_filter(data)
        print data
        
        f = prepare_present_in_child(data)

        self.assertFalse(f('prbF'))
        self.assertTrue(f('prbM'))
        self.assertFalse(f('sibF'))
        self.assertTrue(f('sibM'))
        self.assertTrue(f('prbMsibM'))
        self.assertTrue(f('prbMsibF'))
        self.assertFalse(f('prbFsibM'))
        self.assertFalse(f('prbFsibF'))
        
        self.assertTrue(f(''))


    def test_autism_only_and_unaffected_only_and_autism_and_unaffected_neither_gender_female(self):
        data = {
            'presentInChild':'autism only,unaffected only,autism and unaffected,neither',
            'gender': 'female',
        }
        prepare_gender_filter(data)
        print data
        
        f = prepare_present_in_child(data)

        self.assertTrue(f('prbF'))
        self.assertFalse(f('prbM'))
        self.assertTrue(f('sibF'))
        self.assertFalse(f('sibM'))
        self.assertFalse(f('prbMsibM'))
        self.assertFalse(f('prbMsibF'))
        self.assertTrue(f('prbFsibM'))
        self.assertTrue(f('prbFsibF'))
        
        self.assertTrue(f(''))

        