import unittest
import logging

logger = logging.getLogger(__name__)

from query_prepare import prepare_denovo_phenotype_gender_filter1

class PrepareDenovoPhenotypeGenderFilterAutismStudyTests(unittest.TestCase):

    def test_autism_gender_female(self):
        data = {
            'phenoType': set(['autism']),
            'gender': ['F']
        }
        studyPhenoType = 'autism'
        
        f = prepare_denovo_phenotype_gender_filter1(data, studyPhenoType)

        self.assertTrue(f('prbF'))
        self.assertFalse(f('prbM'))
        self.assertFalse(f('sibF'))
        self.assertFalse(f('sibM'))
        self.assertFalse(f('prbMsibM'))
        self.assertFalse(f('prbMsibF'))
        self.assertTrue(f('prbFsibM'))
        self.assertTrue(f('prbFsibF'))
        self.assertFalse(f(''))

    def test_autism_gender_male(self):
        data = {
            'phenoType': set(['autism']),
            'gender': ['M']
        }
        studyPhenoType = 'autism'
        
        f = prepare_denovo_phenotype_gender_filter1(data, studyPhenoType)

        self.assertFalse(f('prbF'))
        self.assertTrue(f('prbM'))
        self.assertFalse(f('sibF'))
        self.assertFalse(f('sibM'))
        self.assertTrue(f('prbMsibM'))
        self.assertTrue(f('prbMsibF'))
        self.assertFalse(f('prbFsibM'))
        self.assertFalse(f('prbFsibF'))
        self.assertFalse(f(''))

    def test_autism_gender_female_and_male(self):
        data = {
            'phenoType': set(['autism']),
            'gender': ['F', 'M']
        }
        studyPhenoType = 'autism'
        
        f = prepare_denovo_phenotype_gender_filter1(data, studyPhenoType)

        self.assertTrue(f('prbF'))
        self.assertTrue(f('prbM'))
        self.assertFalse(f('sibF'))
        self.assertFalse(f('sibM'))
        self.assertTrue(f('prbMsibM'))
        self.assertTrue(f('prbMsibF'))
        self.assertTrue(f('prbFsibM'))
        self.assertTrue(f('prbFsibF'))
        self.assertFalse(f(''))

    def test_autism_unaffected_gender_male(self):
        data = {
            'phenoType': set(['autism', 'unaffected']),
            'gender': ['M']
        }
        studyPhenoType = 'autism'
        
        f = prepare_denovo_phenotype_gender_filter1(data, studyPhenoType)

        self.assertFalse(f('prbF'))
        self.assertTrue(f('prbM'))
        self.assertFalse(f('sibF'))
        self.assertTrue(f('sibM'))
        self.assertTrue(f('prbMsibM'))
        self.assertTrue(f('prbMsibF'))
        self.assertTrue(f('prbFsibM'))
        self.assertFalse(f('prbFsibF'))
        self.assertFalse(f(''))

    def test_autism_unaffected_gender_female(self):
        data = {
            'phenoType': set(['autism', 'unaffected']),
            'gender': ['F']
        }
        studyPhenoType = 'autism'
        
        f = prepare_denovo_phenotype_gender_filter1(data, studyPhenoType)

        self.assertTrue(f('prbF'))
        self.assertFalse(f('prbM'))
        self.assertTrue(f('sibF'))
        self.assertFalse(f('sibM'))
        self.assertFalse(f('prbMsibM'))
        self.assertTrue(f('prbMsibF'))
        self.assertTrue(f('prbFsibM'))
        self.assertTrue(f('prbFsibF'))
        self.assertFalse(f(''))

    def test_autism_unaffected_gender_female_male(self):
        data = {
            'phenoType': set(['autism', 'unaffected']),
            'gender': ['F', 'M']
        }
        studyPhenoType = 'autism'
        
        f = prepare_denovo_phenotype_gender_filter1(data, studyPhenoType)

        self.assertTrue(f('prbF'))
        self.assertTrue(f('prbM'))
        self.assertTrue(f('sibF'))
        self.assertTrue(f('sibM'))
        self.assertTrue(f('prbMsibM'))
        self.assertTrue(f('prbMsibF'))
        self.assertTrue(f('prbFsibM'))
        self.assertTrue(f('prbFsibF'))
        self.assertFalse(f(''))

class PrepareDenovoPhenotypeGenderFilterSchizophreniaStudyTests(unittest.TestCase):

    def test_autism_gender_female(self):
        data = {
            'phenoType': set(['autism']),
            'gender': ['F']
        }
        studyPhenoType = 'schizophrenia'
        
        f = prepare_denovo_phenotype_gender_filter1(data, studyPhenoType)
        self.assertIsNone(f)
        
        # self.assertTrue(f('prbF'))
        # self.assertFalse(f('prbM'))
        # self.assertFalse(f('sibF'))
        # self.assertFalse(f('sibM'))
        # self.assertFalse(f('prbMsibM'))
        # self.assertFalse(f('prbMsibF'))
        # self.assertTrue(f('prbFsibM'))
        # self.assertTrue(f('prbFsibF'))
        # self.assertFalse(f(''))

    def test_autism_gender_male(self):
        data = {
            'phenoType': set(['autism']),
            'gender': ['M']
        }
        studyPhenoType = 'schizophrenia'
        
        f = prepare_denovo_phenotype_gender_filter1(data, studyPhenoType)
        self.assertIsNone(f)

    def test_autism_gender_female_and_male(self):
        data = {
            'phenoType': set(['autism']),
            'gender': ['F', 'M']
        }
        studyPhenoType = 'schizophrenia'
        
        f = prepare_denovo_phenotype_gender_filter1(data, studyPhenoType)
        self.assertIsNone(f)

    def test_autism_unaffected_gender_male(self):
        data = {
            'phenoType': set(['autism', 'unaffected']),
            'gender': ['M']
        }
        studyPhenoType = 'schizophrenia'
        
        f = prepare_denovo_phenotype_gender_filter1(data, studyPhenoType)

        self.assertFalse(f('prbF'))
        self.assertFalse(f('prbM'))
        self.assertFalse(f('sibF'))
        self.assertTrue(f('sibM'))
        self.assertTrue(f('prbMsibM'))
        self.assertFalse(f('prbMsibF'))
        self.assertTrue(f('prbFsibM'))
        self.assertFalse(f('prbFsibF'))
        self.assertFalse(f(''))

    def test_autism_unaffected_gender_female(self):
        studyPhenoType = 'schizophrenia'
        data = {
            'phenoType': set(['autism', 'unaffected']),
            'gender': ['F']
        }
        
        f = prepare_denovo_phenotype_gender_filter1(data, studyPhenoType)

        self.assertFalse(f('prbF'))
        self.assertFalse(f('prbM'))
        self.assertTrue(f('sibF'))
        self.assertFalse(f('sibM'))
        self.assertFalse(f('prbMsibM'))
        self.assertTrue(f('prbMsibF'))
        self.assertFalse(f('prbFsibM'))
        self.assertTrue(f('prbFsibF'))
        self.assertFalse(f(''))

    def test_autism_unaffected_gender_female_male(self):
        data = {
            'phenoType': set(['autism', 'unaffected']),
            'gender': ['F', 'M']
        }
        studyPhenoType = 'schizophrenia'
        
        f = prepare_denovo_phenotype_gender_filter1(data, studyPhenoType)

        self.assertFalse(f('prbF'))
        self.assertFalse(f('prbM'))
        self.assertTrue(f('sibF'))
        self.assertTrue(f('sibM'))
        self.assertTrue(f('prbMsibM'))
        self.assertTrue(f('prbMsibF'))
        self.assertTrue(f('prbFsibM'))
        self.assertTrue(f('prbFsibF'))
        self.assertFalse(f(''))
