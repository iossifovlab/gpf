'''
Created on Jun 18, 2015

@author: lubo
'''
import unittest
from query_prepare import prepare_denovo_study_type, \
    prepare_denovo_phenotype_gender_filter1
from DAE import vDB


class Test(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def test_prepare_denovo_study_type_single(self):
        data = {'studyType':'WE'}
        
        prepare_denovo_study_type(data)
        self.assertEqual(set(['WE']), data['studyType'])

    
    def test_prepare_denovo_study_type_many(self):
        data = {'studyType':'WE,TG,CNV'}
        
        prepare_denovo_study_type(data)
        self.assertEqual(set(['WE','TG','CNV']), data['studyType'])


    def test_prepare_denovo_study_type_bad(self):
        data = {'studyType':'ala,bala,portokala'}
        
        prepare_denovo_study_type(data)
        self.assertNotIn('studyType', data)

    def test_prepare_denovo_study_type_good_and_bad(self):
        data = {'studyType':'ala,bala,portokala,WE,TG'}
        
        prepare_denovo_study_type(data)
        self.assertEqual(set(['WE','TG']), data['studyType'])

class PrepareDenovoStudyTypeTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(PrepareDenovoStudyTypeTests, cls).setUpClass()
        cls.WE = vDB.get_study('IossifovWE2014')
        cls.TG = vDB.get_study('EichlerTG2012')
        
    def test_autism_and_study_type(self):
        data = {
            'phenoType': set(['autism']),
            'gender': ['F'],
            'studyType': set(['WE'])
        }
        # studyPhenoType = 'autism'
        
        f = prepare_denovo_phenotype_gender_filter1(data, self.WE)
        self.assertTrue(f)

        f = prepare_denovo_phenotype_gender_filter1(data, self.TG)
        self.assertFalse(f)


    def test_unaffected_and_study_type(self):
        data = {
            'phenoType': set(['unaffected']),
            'gender': ['F'],
            'studyType': set(['WE'])
        }
        
        f = prepare_denovo_phenotype_gender_filter1(data, self.WE)
        self.assertTrue(f)

        f = prepare_denovo_phenotype_gender_filter1(data, self.TG)
        self.assertFalse(f)
        
    
