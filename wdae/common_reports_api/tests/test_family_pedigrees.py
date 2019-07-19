'''
Created on May 14, 2018

@author: lubo
'''
from users_api.tests.base_tests import BaseAuthenticatedUserTest
from common_reports_api.variants import StudyVariantReports
from tests.pytest_marks import slow


@slow
class Test(BaseAuthenticatedUserTest):

    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass()
        cls.vr = StudyVariantReports('TESTdenovo_db')
        cls.vr.build()

    def setUp(self):
        self.data = self.vr.serialize()
        vr = StudyVariantReports('TESTdenovo_db')
        vr.deserialize(self.data)
        fr = vr.families_report
        self.fc = fr.get_families_counters('autism')

    def test_family_configuration(self):
        (_p, c) = self.fc.get_counter('prbUprbUprbU')
        self.assertEqual(3, c)

    def test_family_pedigree(self):
        prbMsibF = [
            ['f1', 'p1', '', '', 'F', '#ffffff', 0, 0],
            ['f1', 'p2', '', '', 'M', '#ffffff', 0, 0],
            ['f1', 'p3', 'p1', 'p2', 'M', '#e35252', 0, 0],
        ]
        pedigree = self.fc.family_configuration_to_pedigree_v3(
            'momFdadMprbM')
        self.assertEqual(prbMsibF, pedigree)

        prbMsibF = [
            ['f1', 'p1', '', '', 'F', '#ffffff', 0, 0],
            ['f1', 'p2', '', '', 'M', '#ffffff', 0, 0],
            ['f1', 'p3', 'p1', 'p2', 'M', '#e35252', 0, 0],
            ['f1', 'p4', 'p1', 'p2', 'F', '#ffffff', 0, 0],
        ]
        pedigree = self.fc.family_configuration_to_pedigree_v3(
            'momFdadMprbMsibF')
        self.assertEqual(prbMsibF, pedigree)

        prbUprbUprbU = [
            ['f1', 'p1', '', '', 'U', '#e35252', 0, 0],
            ['f1', 'p2', '', '', 'U', '#e35252', 0, 0],
            ['f1', 'p3', '', '', 'U', '#e35252', 0, 0],
        ]
        pedigree = self.fc.family_configuration_to_pedigree_v3("prbUprbUprbU")
        print(pedigree)
        self.assertEqual(prbUprbUprbU, pedigree)
