'''
Created on Jul 31, 2015

@author: lubo
'''
import unittest
from common_reports_api.variants import StudyVariantReports


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass()
        cls.vr = StudyVariantReports('IossifovWE2014')
        cls.vr.build()

    def setUp(self):
        self.data = self.vr.serialize()

    def tearDown(self):
        pass

    def test_variant_reports_serialize_not_none(self):
        self.assertTrue(self.data)

    def test_variant_reports_serialize_has_study_name(self):
        self.assertIn('study_name', self.data)
        self.assertEquals('IossifovWE2014', self.data['study_name'])

    def test_variant_reports_serialize_has_families_report(self):
        self.assertIn('families_report', self.data)

    def test_variant_reports_serialize_has_denovo_report(self):
        self.assertIn('denovo_report', self.data)

    def test_variant_reports_deserialize(self):
        vr = StudyVariantReports('IossifovWE2014')
        vr.deserialize(self.data)
        self.assertTrue(vr.families_report)
        self.assertTrue(vr.denovo_report)

    def test_deserialize_family_reports_children_counters(self):
        vr = StudyVariantReports('IossifovWE2014')
        vr.deserialize(self.data)
        fr = vr.families_report
        cc = fr.get_children_counters('autism')
        self.assertEquals(2166, cc.children_male)
        self.assertEquals(341, cc.children_female)

        cc = fr.get_children_counters('unaffected')
        self.assertEquals(899, cc.children_male)
        self.assertEquals(1011, cc.children_female)

    def test_deserialize_family_reports_family_counters(self):
        vr = StudyVariantReports('IossifovWE2014')
        vr.deserialize(self.data)
        fr = vr.families_report
        fc = fr.get_families_counters('autism')
        tc = fc.type_counters()
        self.assertTrue(tc)

        (_p, c) = fc.get_counter('dadMmomFprbMsibF')
        self.assertEqual(877, c)
        (_p, c) = fc.get_counter('dadMmomFprbMsibM')
        self.assertEqual(789, c)
        (_p, c) = fc.get_counter('dadMmomFprbM')
        self.assertEqual(500, c)
        (_p, c) = fc.get_counter('dadMmomFprbFsibF')
        self.assertEqual(128, c)
        (_p, c) = fc.get_counter('dadMmomFprbFsibM')
        self.assertEqual(107, c)
        (_p, c) = fc.get_counter('dadMmomFprbF')
        self.assertEqual(106, c)
        (_p, c) = fc.get_counter('dadMmomFsibF')
        self.assertEqual(6, c)
        (_p, c) = fc.get_counter('dadMmomFsibM')
        self.assertEqual(3, c)

        fc = fr.get_families_counters('unaffected')
        self.assertIsNone(fc)

    def test_deserialize_denovo_reports_autism_not_none(self):
        vr = StudyVariantReports('IossifovWE2014')
        vr.deserialize(self.data)
        dr = vr.denovo_report
        self.assertTrue(dr)
        self.assertIn('LGDs', dr.rows[0].effect_type)
        self.assertIn('Synonymous', dr.rows[11].effect_type)

    def test_deserialize_denovo_reports_phenotypes(self):
        vr = StudyVariantReports('IossifovWE2014')
        vr.deserialize(self.data)
        self.assertEquals(vr.phenotypes, ['autism', 'unaffected'])

    def test_deserialize_denovo_reports_effect_groups(self):
        vr = StudyVariantReports('IossifovWE2014')
        vr.deserialize(self.data)
        dr = vr.denovo_report

        effect_groups = dr.rows
        de = effect_groups[0].row[0]
        self.assertEqual('autism', de.phenotype)
        # FIXME: changed after rennotation
        # self.assertEquals(383, de.events_count)
        self.assertEquals(388, de.events_count)
        # self.assertEquals(357, de.events_children_count)
        self.assertEquals(362, de.events_children_count)

        de = effect_groups[0].row[1]
        self.assertEqual('unaffected', de.phenotype)
        self.assertEquals(178, de.events_count)
        self.assertEquals(169, de.events_children_count)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
