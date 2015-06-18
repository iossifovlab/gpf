'''
Created on Jun 18, 2015

@author: lubo
'''
import unittest
from api.query.query_prepare import prepare_denovo_study_type


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

