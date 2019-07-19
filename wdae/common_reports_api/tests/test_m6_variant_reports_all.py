'''
Created on Jul 31, 2015

@author: lubo
'''
import unittest
from common_reports_api.variants import VariantReports
from tests.pytest_marks import slow


@slow
class Test(unittest.TestCase):
    TEST_WHOLE_EXOME = [
        'SD_TEST',
        'TEST WHOLE EXOME',
        'IossifovWE2014',
        'EichlerTG2012',
        'ACS2014',
        'KarayiorgouWE2012',
        'GulsunerSchWE2013',
        'ODonovanWE2014',
        'StromWE2012',
        'VissersWE2012',
        'Lifton2013CHD',
        'Chung2015CHD',
        'Epi4KWE2013',
        'ORoakTG2014-SSC',
        'ORoakTG2014-TASC',
        'Krumm2015-SNVindel',
    ]

    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass()
        cls.vr = VariantReports(studies=cls.TEST_WHOLE_EXOME)
        cls.vr.precompute()
        cls.data = cls.vr.serialize()

    def setUp(self):
        self.vr = VariantReports(studies=self.TEST_WHOLE_EXOME)
        self.vr.deserialize(self.data)

    def tearDown(self):
        pass

    def test_serialize_deserialize_not_none(self):
        self.assertIsNotNone(self.data)

    def test_deserialize(self):
        self.assertIsNotNone(self.vr.data)

    def test_deserialize_all_we_study(self):
        sr = self.vr['TEST WHOLE EXOME']
        self.assertIsNotNone(sr)
        self.assertIsNotNone(sr.families_report)
        self.assertIsNotNone(sr.denovo_report)

    def test_deserialize_lifton_study(self):
        sr = self.vr['Lifton2013CHD']
        self.assertIsNotNone(sr)
        self.assertIsNotNone(sr.families_report)
        self.assertIsNotNone(sr.denovo_report)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.test_']
    unittest.main()
