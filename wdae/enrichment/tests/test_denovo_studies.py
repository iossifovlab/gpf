'''
Created on Sep 29, 2016

@author: lubo
'''
import unittest
from enrichment.counters import DenovoStudies
from enrichment.config import PHENOTYPES


class DenovoStudiesTest(unittest.TestCase):

    def test_unaffected(self):
        denovo_studies = DenovoStudies()
        studies = denovo_studies.get_studies('unaffected')

        for st in studies:
            assert 'WE' == st.get_attr('study.type')
            assert st.get_attr('study.phenotype') in PHENOTYPES

    def test_autism(self):
        denovo_studies = DenovoStudies()
        studies = denovo_studies.get_studies('autism')

        for st in studies:
            assert 'WE' == st.get_attr('study.type')
            assert 'autism' == st.get_attr('study.phenotype')

    def test_bad_phenotype(self):
        with self.assertRaises(AssertionError):
            denovo_studies = DenovoStudies()
            denovo_studies.get_studies('ala bala')
