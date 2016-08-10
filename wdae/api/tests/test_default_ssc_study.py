'''
Created on Apr 26, 2016

@author: lubo
'''
import unittest
from helpers.default_ssc_study import get_ssc_all, get_ssc_denovo,\
    get_ssc_transmitted, get_ssc_denovo_studies, get_ssc_transmitted_studies


class Test(unittest.TestCase):

    def test_default_ssc_all(self):
        res = get_ssc_all()
        self.assertIn('denovoStudies', res)
        self.assertIn('transmittedStudies', res)

    def test_default_ssc_denovo(self):
        res = get_ssc_denovo()
        self.assertIsNotNone(res)

    def test_default_ssc_denovo_has_denovo(self):
        res = get_ssc_denovo_studies()
        for st in res:
            self.assertFalse(st.has_transmitted)
            self.assertTrue(st.has_denovo)

    def test_default_ssc_transmitted(self):
        res = get_ssc_transmitted()
        self.assertIsNotNone(res)

    def test_default_ssc_transmitted_has_transmitted(self):
        res = get_ssc_transmitted_studies()
        for st in res:
            self.assertTrue(st.has_transmitted)
            self.assertFalse(st.has_denovo)

if __name__ == "__main__":
    unittest.main()
