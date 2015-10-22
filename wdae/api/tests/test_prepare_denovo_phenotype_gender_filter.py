import unittest

from query_prepare import prepare_denovo_phenotype_gender_filter1, \
    prepare_gender_filter
from DAE import vDB
from VariantsDB import Study


class PrepareDenovoPhenotypeGenderFilterAutismStudyTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(PrepareDenovoPhenotypeGenderFilterAutismStudyTests, cls).\
            setUpClass()
        cls.STUDY = vDB.get_study('IossifovWE2014')

    def test_autism_gender_female(self):
        data = {
            'phenoType': set(['autism']),
            'gender': ['F']
        }
        # studyPhenoType = 'autism'
        present_in_child = \
            prepare_denovo_phenotype_gender_filter1(data, self.STUDY)
        gender = prepare_gender_filter(data)

        f = Study._present_in_child_filter(present_in_child, gender)
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
        # studyPhenoType = 'autism'
        present_in_child = \
            prepare_denovo_phenotype_gender_filter1(data, self.STUDY)
        gender = prepare_gender_filter(data)

        f = Study._present_in_child_filter(present_in_child, gender)

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
        # studyPhenoType = 'autism'
        present_in_child = \
            prepare_denovo_phenotype_gender_filter1(data, self.STUDY)
        gender = prepare_gender_filter(data)

        f = Study._present_in_child_filter(present_in_child, gender)

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
        # studyPhenoType = 'autism'
        present_in_child = \
            prepare_denovo_phenotype_gender_filter1(data, self.STUDY)
        gender = prepare_gender_filter(data)

        f = Study._present_in_child_filter(present_in_child, gender)

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
        # studyPhenoType = 'autism'
        present_in_child = \
            prepare_denovo_phenotype_gender_filter1(data, self.STUDY)
        gender = prepare_gender_filter(data)

        f = Study._present_in_child_filter(present_in_child, gender)

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
        # studyPhenoType = 'autism'
        present_in_child = \
            prepare_denovo_phenotype_gender_filter1(data, self.STUDY)
        gender = prepare_gender_filter(data)

        f = Study._present_in_child_filter(present_in_child, gender)

        self.assertTrue(f('prbF'))
        self.assertTrue(f('prbM'))
        self.assertTrue(f('sibF'))
        self.assertTrue(f('sibM'))
        self.assertTrue(f('prbMsibM'))
        self.assertTrue(f('prbMsibF'))
        self.assertTrue(f('prbFsibM'))
        self.assertTrue(f('prbFsibF'))
        self.assertFalse(f(''))


class PrepareDenovoPhenotypeGenderFilterSchizophreniaTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(PrepareDenovoPhenotypeGenderFilterSchizophreniaTests, cls).\
            setUpClass()
        cls.STUDY = vDB.get_study('KarayiorgouWE2012')

    def test_autism_gender_female(self):
        data = {
            'phenoType': set(['autism']),
            'gender': ['F']
        }
        # studyPhenoType = 'schizophrenia'
        present_in_child = \
            prepare_denovo_phenotype_gender_filter1(data, self.STUDY)
        self.assertIsNone(present_in_child)

    def test_autism_gender_male(self):
        data = {
            'phenoType': set(['autism']),
            'gender': ['M']
        }
        # studyPhenoType = 'schizophrenia'
        present_in_child = \
            prepare_denovo_phenotype_gender_filter1(data, self.STUDY)
        self.assertIsNone(present_in_child)

    def test_autism_gender_female_and_male(self):
        data = {
            'phenoType': set(['autism']),
            'gender': ['F', 'M']
        }
        # studyPhenoType = 'schizophrenia'
        present_in_child = \
            prepare_denovo_phenotype_gender_filter1(data, self.STUDY)
        self.assertIsNone(present_in_child)

    def test_autism_unaffected_gender_male(self):
        data = {
            'phenoType': set(['autism', 'unaffected']),
            'gender': ['M']
        }
        # studyPhenoType = 'schizophrenia'
        present_in_child = \
            prepare_denovo_phenotype_gender_filter1(data, self.STUDY)
        gender = prepare_gender_filter(data)
        self.assertIsNotNone(present_in_child)

        f = Study._present_in_child_filter(present_in_child, gender)

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
        # studyPhenoType = 'schizophrenia'
        data = {
            'phenoType': set(['autism', 'unaffected']),
            'gender': ['F']
        }
        present_in_child = \
            prepare_denovo_phenotype_gender_filter1(data, self.STUDY)
        gender = prepare_gender_filter(data)
        self.assertIsNotNone(present_in_child)

        f = Study._present_in_child_filter(present_in_child, gender)

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
        present_in_child = \
            prepare_denovo_phenotype_gender_filter1(data, self.STUDY)
        gender = prepare_gender_filter(data)
        self.assertIsNotNone(present_in_child)

        f = Study._present_in_child_filter(present_in_child, gender)

        self.assertFalse(f('prbF'))
        self.assertFalse(f('prbM'))
        self.assertTrue(f('sibF'))
        self.assertTrue(f('sibM'))
        self.assertTrue(f('prbMsibM'))
        self.assertTrue(f('prbMsibF'))
        self.assertTrue(f('prbFsibM'))
        self.assertTrue(f('prbFsibF'))
        self.assertFalse(f(''))
