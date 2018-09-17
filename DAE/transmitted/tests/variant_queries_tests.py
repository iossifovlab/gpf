'''
Created on Oct 22, 2015

@author: lubo
'''
from __future__ import unicode_literals
import unittest

from Variant import present_in_child_filter
from VariantsDB import Study
from query_prepare import prepare_gender_filter
from query_variants import prepare_present_in_child


class PresentInChildFilterTest(unittest.TestCase):

    def test_autism_only(self):
        f = present_in_child_filter(
            ['autism only'])
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
        f = present_in_child_filter(
            ['unaffected only'])
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
        f = present_in_child_filter(
            ['autism and unaffected'])
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
        f = present_in_child_filter(
            ['neither'])
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
        f = present_in_child_filter(
            ['autism only', 'unaffected only'])
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
        f = present_in_child_filter(
            ['autism only', 'unaffected only', 'autism and unaffected'])
        self.assertTrue(f('prbF'))
        self.assertTrue(f('prbM'))
        self.assertTrue(f('sibF'))
        self.assertTrue(f('sibM'))
        self.assertTrue(f('prbMsibM'))
        self.assertTrue(f('prbMsibF'))
        self.assertTrue(f('prbFsibM'))
        self.assertTrue(f('prbFsibF'))
        self.assertFalse(f(''))

    def test_all_pheno(self):
        f = present_in_child_filter(
            ['autism only', 'unaffected only', 'autism and unaffected',
             'neither'])
        self.assertIsNone(f)

    def test_autism_only_gender_male(self):
        data = {
            'presentInChild': 'autism only',
            'gender': 'male'
        }
        gender = prepare_gender_filter(data)
        present_in_child = prepare_present_in_child(data)
        f = present_in_child_filter(present_in_child, gender)

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
            'presentInChild': 'autism only',
            'gender': 'female'
        }
        gender = prepare_gender_filter(data)
        present_in_child = prepare_present_in_child(data)
        f = present_in_child_filter(present_in_child, gender)

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
            'presentInChild': 'autism only',
            'gender': 'male,female'
        }
        gender = prepare_gender_filter(data)
        present_in_child = prepare_present_in_child(data)
        f = present_in_child_filter(present_in_child, gender)

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
            'presentInChild': 'unaffected only',
            'gender': 'male'
        }
        gender = prepare_gender_filter(data)
        present_in_child = prepare_present_in_child(data)
        f = present_in_child_filter(present_in_child, gender)

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
            'presentInChild': 'unaffected only',
            'gender': 'female'
        }
        gender = prepare_gender_filter(data)
        present_in_child = prepare_present_in_child(data)
        f = present_in_child_filter(present_in_child, gender)

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
            'presentInChild': 'unaffected only',
            'gender': 'male,female'
        }
        gender = prepare_gender_filter(data)
        present_in_child = prepare_present_in_child(data)
        f = present_in_child_filter(present_in_child, gender)

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
            'presentInChild': 'autism and unaffected',
            'gender': 'male'
        }
        gender = prepare_gender_filter(data)
        present_in_child = prepare_present_in_child(data)
        f = present_in_child_filter(present_in_child, gender)

        self.assertFalse(f('prbF'))
        self.assertFalse(f('prbM'))
        self.assertFalse(f('sibF'))
        self.assertFalse(f('sibM'))
        self.assertTrue(f('prbMsibM'))
        self.assertTrue(f('prbMsibF'))
        self.assertTrue(f('prbFsibM'))
        self.assertFalse(f('prbFsibF'))
        self.assertFalse(f(''))

    def test_autism_and_unaffected_gender_female(self):
        data = {
            'presentInChild': 'autism and unaffected',
            'gender': 'female'
        }
        gender = prepare_gender_filter(data)
        present_in_child = prepare_present_in_child(data)
        f = present_in_child_filter(present_in_child, gender)

        self.assertFalse(f('prbF'))
        self.assertFalse(f('prbM'))
        self.assertFalse(f('sibF'))
        self.assertFalse(f('sibM'))
        self.assertFalse(f('prbMsibM'))
        self.assertTrue(f('prbMsibF'))
        self.assertTrue(f('prbFsibM'))
        self.assertTrue(f('prbFsibF'))
        self.assertFalse(f(''))

    def test_autism_and_unaffected_gender_male_and_female(self):
        data = {
            'presentInChild': 'autism and unaffected',
            'gender': 'female'
        }
        gender = prepare_gender_filter(data)
        present_in_child = prepare_present_in_child(data)
        f = present_in_child_filter(present_in_child, gender)

        self.assertFalse(f('prbF'))
        self.assertFalse(f('prbM'))
        self.assertFalse(f('sibF'))
        self.assertFalse(f('sibM'))
        self.assertFalse(f('prbMsibM'))
        self.assertTrue(f('prbMsibF'))
        self.assertTrue(f('prbFsibM'))
        self.assertTrue(f('prbFsibF'))
        self.assertFalse(f(''))

    def test_neither_gender_male(self):
        data = {
            'presentInChild': 'neither',
            'gender': 'male'
        }
        gender = prepare_gender_filter(data)
        present_in_child = prepare_present_in_child(data)
        f = present_in_child_filter(present_in_child, gender)

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
            'presentInChild': 'neither',
            'gender': 'female'
        }
        gender = prepare_gender_filter(data)
        present_in_child = prepare_present_in_child(data)
        f = present_in_child_filter(present_in_child, gender)

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
            'presentInChild': 'neither',
            'gender': 'male,female'
        }
        gender = prepare_gender_filter(data)
        present_in_child = prepare_present_in_child(data)
        f = present_in_child_filter(present_in_child, gender)

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
            'presentInChild': 'autism only,unaffected only',
            'gender': 'male'
        }
        gender = prepare_gender_filter(data)
        present_in_child = prepare_present_in_child(data)
        f = present_in_child_filter(present_in_child, gender)

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
            'presentInChild': 'autism only,unaffected only',
            'gender': 'female'
        }
        gender = prepare_gender_filter(data)
        present_in_child = prepare_present_in_child(data)
        f = present_in_child_filter(present_in_child, gender)

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
            'presentInChild': 'autism only,unaffected only',
            'gender': 'male,female'
        }
        gender = prepare_gender_filter(data)
        present_in_child = prepare_present_in_child(data)
        f = present_in_child_filter(present_in_child, gender)

        self.assertTrue(f('prbF'))
        self.assertTrue(f('prbM'))
        self.assertTrue(f('sibF'))
        self.assertTrue(f('sibM'))
        self.assertFalse(f('prbMsibM'))
        self.assertFalse(f('prbMsibF'))
        self.assertFalse(f('prbFsibM'))
        self.assertFalse(f('prbFsibF'))
        self.assertFalse(f(''))

    def test_autism_and_unaffected_and_autism_and_uaffected_male(self):
        data = {
            'presentInChild':
            'autism only,unaffected only,autism and unaffected',
            'gender': 'male',
        }
        gender = prepare_gender_filter(data)
        present_in_child = prepare_present_in_child(data)
        f = present_in_child_filter(present_in_child, gender)

        self.assertFalse(f('prbF'))
        self.assertTrue(f('prbM'))
        self.assertFalse(f('sibF'))
        self.assertTrue(f('sibM'))
        self.assertTrue(f('prbMsibM'))
        self.assertTrue(f('prbMsibF'))
        self.assertTrue(f('prbFsibM'))
        self.assertFalse(f('prbFsibF'))
        self.assertFalse(f(''))

    def test_autism_and_unaffected_and_autism_and_uaffected_female(self):
        data = {
            'presentInChild':
            'autism only,unaffected only,autism and unaffected',
            'gender': 'female',
        }
        gender = prepare_gender_filter(data)
        present_in_child = prepare_present_in_child(data)
        f = present_in_child_filter(present_in_child, gender)

        self.assertTrue(f('prbF'))
        self.assertFalse(f('prbM'))
        self.assertTrue(f('sibF'))
        self.assertFalse(f('sibM'))
        self.assertFalse(f('prbMsibM'))
        self.assertTrue(f('prbMsibF'))
        self.assertTrue(f('prbFsibM'))
        self.assertTrue(f('prbFsibF'))
        self.assertFalse(f(''))

    def test_autism_and_unaffected_and_autism_and_uaffected_male_and_female(
            self):
        data = {
            'presentInChild':
            'autism only,unaffected only,autism and unaffected',
            'gender': 'male,female',
        }
        gender = prepare_gender_filter(data)
        present_in_child = prepare_present_in_child(data)
        f = present_in_child_filter(present_in_child, gender)

        self.assertTrue(f('prbF'))
        self.assertTrue(f('prbM'))
        self.assertTrue(f('sibF'))
        self.assertTrue(f('sibM'))
        self.assertTrue(f('prbMsibM'))
        self.assertTrue(f('prbMsibF'))
        self.assertTrue(f('prbFsibM'))
        self.assertTrue(f('prbFsibF'))
        self.assertFalse(f(''))

    def test_pheno_all_gender_male(self):
        data = {
            'presentInChild':
            'autism only,unaffected only,autism and unaffected,neither',
            'gender': 'male',
        }
        gender = prepare_gender_filter(data)
        present_in_child = prepare_present_in_child(data)
        f = present_in_child_filter(present_in_child, gender)

        self.assertFalse(f('prbF'))
        self.assertTrue(f('prbM'))
        self.assertFalse(f('sibF'))
        self.assertTrue(f('sibM'))
        self.assertTrue(f('prbMsibM'))
        self.assertTrue(f('prbMsibF'))
        self.assertTrue(f('prbFsibM'))
        self.assertFalse(f('prbFsibF'))

        self.assertFalse(f(''))

    def test_pheno_all_gender_female(self):
        data = {
            'presentInChild':
            'autism only,unaffected only,autism and unaffected,neither',
            'gender': 'female',
        }
        gender = prepare_gender_filter(data)
        present_in_child = prepare_present_in_child(data)
        f = present_in_child_filter(present_in_child, gender)

        self.assertTrue(f('prbF'))
        self.assertFalse(f('prbM'))
        self.assertTrue(f('sibF'))
        self.assertFalse(f('sibM'))
        self.assertFalse(f('prbMsibM'))
        self.assertTrue(f('prbMsibF'))
        self.assertTrue(f('prbFsibM'))
        self.assertTrue(f('prbFsibF'))

    def test_pheno_all_gender_all(self):
        data = {
            'presentInChild':
            'autism only,unaffected only,autism and unaffected,neither',
            'gender': 'male,female',
        }
        gender = prepare_gender_filter(data)
        present_in_child = prepare_present_in_child(data)
        f = present_in_child_filter(present_in_child, gender)

        self.assertIsNone(f)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
