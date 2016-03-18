'''
Created on Jul 28, 2015

@author: lubo
'''
import unittest
from api.reports.variants import CommonBase, ChildrenCounter, \
    FamiliesReport, FamiliesCounters, DenovoEventsCounter, \
    DenovoEventsReport, StudyVariantReports


class Test(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_effect_types_base(self):
        et = CommonBase.effect_types()
        self.assertEqual(15, len(et),
                         "wrong number of effect types {}".format(len(et)))

    def test_effect_groups_base(self):
        eg = CommonBase.effect_groups()
        self.assertEqual(4, len(eg), "wrong number of effect groups")

    def test_family_report_we_studies(self):
        fr = FamiliesReport('ALL WHOLE EXOME')
        self.assertEqual(14, len(fr.studies))

    def test_family_report_we_phenotypes(self):
        fr = FamiliesReport('ALL WHOLE EXOME')

        self.assertEqual(6, len(fr.phenotypes))
        self.assertEquals(['autism',
                           'congenital heart disease',
                           'epilepsy',
                           'intelectual disability',
                           'schizophrenia',
                           'unaffected'], fr.phenotypes)

    def test_family_report_ssc_studies(self):
        fr = FamiliesReport('ALL SSC')
        self.assertEqual(7, len(fr.studies))

    def test_family_report_ssc_phenotypes(self):
        fr = FamiliesReport('ALL SSC')

        self.assertEqual(2, len(fr.phenotypes))
        self.assertEquals(['autism',
                           'unaffected'], fr.phenotypes)

    def test_family_counters_autism_iossifov(self):
        fr = FamiliesReport('IossifovWE2012')
        fc = ChildrenCounter('autism')
        fc.build(fr.studies)

        self.assertEqual(314, fc.children_male)
        self.assertEqual(29, fc.children_female)

    def test_family_counters_uaffected_iossifov(self):
        fr = FamiliesReport('IossifovWE2012')
        fc = ChildrenCounter('unaffected')
        fc.build(fr.studies)

        self.assertEqual(161, fc.children_male)
        self.assertEqual(182, fc.children_female)

    def test_family_counters_bad_phenotype(self):
        with self.assertRaises(ValueError):
            ChildrenCounter('ala-bala-portokala')

    def test_families_report_we_build_does_not_raise(self):
        fr = FamiliesReport('ALL WHOLE EXOME')
        self.assertTrue(fr)

    def test_families_counters_phenotype_test(self):
        fc = FamiliesCounters('autism')
        self.assertTrue(fc)

    def test_families_counters_phenotype_unaffected(self):
        with self.assertRaises(ValueError):
            FamiliesCounters('unaffected')

    def test_families_counters_phenotype_wrong(self):
        with self.assertRaises(ValueError):
            FamiliesCounters('ala-bala-portokala')

    def test_family_configuration_to_pedigree_prbF(self):
        prbF = [["mom", "F", 0],
                ["dad", "M", 0],
                ["prb", "F", 0]]
        pedigree = CommonBase.family_configuration_to_pedigree('prbF')
        self.assertTrue(prbF, pedigree)

    def test_family_configuration_to_pedigree_prbMsibF(self):
        prbMsibF = [["mom", "F", 0],
                    ["dad", "M", 0],
                    ["prb", "M", 0],
                    ["sib", "F", 0]]
        pedigree = CommonBase.family_configuration_to_pedigree('prbMsibF')
        self.assertTrue(prbMsibF, pedigree)

    def test_family_configuration_to_pedigree_prbMsibMsibF(self):
        prbMsibMsibF = [["mom", "F", 0],
                        ["dad", "M", 0],
                        ["prb", "M", 0],
                        ["sib", "M", 0],
                        ["sib", "F", 0]]
        pedigree = CommonBase.family_configuration_to_pedigree('prbMsibMsibF')
        self.assertTrue(prbMsibMsibF, pedigree)

    def test_family_reports_build(self):
        fr = FamiliesReport('ALL SSC')
        self.assertFalse(fr.families_counters)
        self.assertFalse(fr.children_counters)

        fr.build()

        self.assertTrue(fr.families_counters)
        self.assertTrue(fr.children_counters)

    def test_family_reports_serialize_deserialize_we(self):
        fr = FamiliesReport('ALL WHOLE EXOME')
        fr.precompute()

        data = fr.serialize()

        fr1 = FamiliesReport('ALL WHOLE EXOME')
        self.assertFalse(fr1.families_counters)
        self.assertFalse(fr1.children_counters)

        fr1.deserialize(data)

        self.assertTrue(fr1.families_counters)
        self.assertTrue(fr1.children_counters)

    def test_family_reports_serialize_deserialize_ssc_family_counters(self):
        fr = FamiliesReport('ALL SSC')
        fr.precompute()

        data = fr.serialize()

        fr1 = FamiliesReport('ALL SSC')
        fr1.deserialize(data)

        self.assertTrue(fr.get_families_counters('autism'))
        fc = fr.get_families_counters('autism')
        fc1 = fr1.get_families_counters('autism')

        self.assertEquals(fc.type_counters(),
                          fc1.type_counters())

    def test_denovo_counter_autism_iossifov(self):
        fr = FamiliesReport('IossifovWE2014')
        cc = ChildrenCounter('autism')
        cc.build(fr.studies)

        dc = DenovoEventsCounter('autism', cc, 'LGDs')
        dc.build(fr.studies)

        self.assertEqual(383, dc.events_count)
        self.assertEqual(357, dc.events_children_count)
        self.assertAlmostEqual(0.153, dc.events_rate_per_child, 3)
        self.assertAlmostEqual(0.142, dc.events_children_percent, 3)

    def test_denovo_counter_unaffected_iossifov(self):
        fr = FamiliesReport('IossifovWE2014')
        cc = ChildrenCounter('unaffected')
        cc.build(fr.studies)

        dc = DenovoEventsCounter('unaffected', cc, 'LGDs')
        dc.build(fr.studies)

        self.assertEqual(178, dc.events_count)
        self.assertEqual(169, dc.events_children_count)
        self.assertAlmostEqual(0.093, dc.events_rate_per_child, 3)
        self.assertAlmostEqual(0.088, dc.events_children_percent, 3)

    def test_denovo_events_report_iossifov(self):
        fr = FamiliesReport('IossifovWE2014')
        fr.build()

        dr = DenovoEventsReport('IossifovWE2014', fr)
        dr.build()
        self.assertTrue(dr.rows)
        self.assertIn('LGDs', dr.rows)
        self.assertIn('Nonsense', dr.rows)

    def test_study_variant_reports(self):
        vr = StudyVariantReports('IossifovWE2014')
        self.assertFalse(vr.families_report)
        self.assertFalse(vr.denovo_report)

        vr.build()
        self.assertTrue(vr.families_report)
        self.assertTrue(vr.denovo_report)

    def test_children_counters_we_studies(self):
        fr = FamiliesReport('ALL WHOLE EXOME')
        fr.build()
        cc = fr.get_children_counters('unaffected')
        self.assertEquals(1464, cc.children_male)
        self.assertEquals(1566, cc.children_female)

    def test_children_counters_lifton_studies(self):
        fr = FamiliesReport('Lifton2013CHD')
        fr.build()
        cc = fr.get_children_counters('unaffected')
        self.assertEquals(133, cc.children_male)
        self.assertEquals(131, cc.children_female)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
