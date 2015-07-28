'''
Created on Jul 28, 2015

@author: lubo
'''
import unittest
from api.reports.variants import ReportBase, FamilyReport


class Test(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_effect_types_base(self):
        et = ReportBase.effect_types()
        self.assertEqual(15, len(et),
                         "wrong number of effect types {}".format(len(et)))

    def test_effect_groups_base(self):
        eg = ReportBase.effect_groups()
        self.assertEqual(3, len(eg), "wrong number of effect groups")

    def test_family_report_we_studies(self):
        fr = FamilyReport('ALL WHOLE EXOME')
        self.assertEqual(10, len(fr.studies))

    def test_family_report_we_phenotypes(self):
        fr = FamilyReport('ALL WHOLE EXOME')

        self.assertEqual(6, len(fr.phenotypes))
        self.assertEquals(['autism',
                           'congenital heart disease',
                           'epilepsy',
                           'intelectual disability',
                           'schizophrenia',
                           'unaffected'], fr.phenotypes)

    def test_family_report_ssc_studies(self):
        fr = FamilyReport('ALL SSC')
        self.assertEqual(3, len(fr.studies))

    def test_family_report_ssc_phenotypes(self):
        fr = FamilyReport('ALL SSC')

        self.assertEqual(2, len(fr.phenotypes))
        self.assertEquals(['autism',
                           'unaffected'], fr.phenotypes)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
