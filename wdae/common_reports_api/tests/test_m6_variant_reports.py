'''
Created on Jul 28, 2015

@author: lubo
'''
from __future__ import unicode_literals
import unittest
from common_reports_api.variants import CommonBase, ChildrenCounter, \
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
        fr = FamiliesReport('TEST WHOLE EXOME')
        self.assertEqual(14, len(fr.studies))

    def test_family_report_we_phenotypes(self):
        fr = FamiliesReport('TEST WHOLE EXOME')
        fr.build()
        self.assertEqual(6, len(fr.phenotypes))
        self.assertEquals(['autism',
                           'congenital heart disease',
                           'epilepsy',
                           'intellectual disability',
                           'schizophrenia',
                           'unaffected'], fr.phenotypes)

    def test_family_report_ssc_studies(self):
        fr = FamiliesReport('ALL SSC')
        self.assertEqual(7, len(fr.studies))

    def test_family_report_ssc_phenotypes(self):
        fr = FamiliesReport('ALL SSC')
        fr.build()
        self.assertEqual(2, len(fr.phenotypes))
        self.assertEquals(['autism', 'unaffected'], fr.phenotypes)

    def test_family_counters_autism_iossifov(self):
        fr = FamiliesReport('IossifovWE2012')
        fc = ChildrenCounter('autism', {
            'autism': {
                'name': 'autism',
                'color': '#e35252'
            }
        })
        fc.build(fr.studies)

        self.assertEqual(314, fc.children_male)
        self.assertEqual(29, fc.children_female)

    def test_family_counters_uaffected_iossifov(self):
        fr = FamiliesReport('IossifovWE2012')
        fc = ChildrenCounter('unaffected', {
            'unaffected': {
                'name': 'unaffected',
                'color': '#ffffff'
            }
        })
        fc.build(fr.studies)

        self.assertEqual(161, fc.children_male)
        self.assertEqual(182, fc.children_female)

    def test_families_report_we_build_does_not_raise(self):
        fr = FamiliesReport('TEST WHOLE EXOME')
        self.assertTrue(fr)

    def test_families_counters_phenotype_test(self):
        fc = FamiliesCounters('autism', {'autism': {'name': 'autism'}})
        self.assertTrue(fc)

    def test_families_counters_phenotype_unaffected(self):
        with self.assertRaises(ValueError):
            FamiliesCounters(
                'unaffected', {'unaffected': {'name': 'unaffected'}})

    def test_families_counters_phenotype_wrong(self):
        with self.assertRaises(ValueError):
            FamiliesCounters('ala-bala-portokala', {})

    def test_family_configuration_to_pedigree_v3_prbMsibF(self):
        fr = FamiliesReport('TEST WHOLE EXOME')
        fc = FamiliesCounters('autism', fr.legend)
        prbMsibF = [
            ['f1', 'p1', '', '', 'F', '#ffffff', 0, 0],
            ['f1', 'p2', '', '', 'M', '#ffffff', 0, 0],
            ['f1', 'p3', 'p1', 'p2', 'M', '#e35252', 0, 0],
            ['f1', 'p4', 'p1', 'p2', 'F', '#ffffff', 0, 0],
        ]
        pedigree = fc.family_configuration_to_pedigree_v3('momFdadMprbMsibF')
        self.assertEqual(prbMsibF, pedigree)

    def test_family_configuration_to_pedigree_v3_prbMsibMsibF(self):
        fr = FamiliesReport('TEST WHOLE EXOME')
        fc = FamiliesCounters('autism', fr.legend)
        prbMsibMsibF = [
            ['f1', 'p1', '', '', 'F', '#ffffff', 0, 0],
            ['f1', 'p2', '', '', 'M', '#ffffff', 0, 0],
            ['f1', 'p3', 'p1', 'p2', 'M', '#e35252', 0, 0],
            ['f1', 'p4', 'p1', 'p2', 'M', '#ffffff', 0, 0],
            ['f1', 'p5', 'p1', 'p2', 'F', '#ffffff', 0, 0]
        ]
        pedigree = fc.family_configuration_to_pedigree_v3(
            'momFdadMprbMsibMsibF')
        self.assertEqual(prbMsibMsibF, pedigree)

    def test_family_reports_build(self):
        fr = FamiliesReport('ALL SSC')
        self.assertFalse(fr.families_counters)
        self.assertFalse(fr.children_counters)

        fr.build()

        self.assertTrue(fr.families_counters)
        self.assertTrue(fr.children_counters)

    def test_family_reports_serialize_deserialize_we(self):
        fr = FamiliesReport('TEST WHOLE EXOME')
        fr.precompute()

        data = fr.serialize()

        fr1 = FamiliesReport('TEST WHOLE EXOME')
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
        cc = ChildrenCounter('autism', fr.legend)
        cc.build(fr.studies)

        dc = DenovoEventsCounter('autism', fr.legend, cc, 'LGDs')
        dc.build(fr.studies)

        # FIXME: changed after rennotation
        # self.assertEqual(383, dc.events_count)
        self.assertEqual(388, dc.events_count)
        # self.assertEqual(357, dc.events_children_count)
        self.assertEqual(362, dc.events_children_count)
        self.assertAlmostEqual(0.155, dc.events_rate_per_child, 3)
        self.assertAlmostEqual(0.144, dc.events_children_percent, 3)

    def test_denovo_counter_unaffected_iossifov(self):
        fr = FamiliesReport('IossifovWE2014')
        cc = ChildrenCounter('unaffected', fr.legend)
        cc.build(fr.studies)

        dc = DenovoEventsCounter('unaffected', fr.legend, cc, 'LGDs')
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
        self.assertEqual('LGDs', dr.rows[0].effect_type)
        # self.assertIn('Nonsense', dr.rows)

    def test_study_variant_reports(self):
        vr = StudyVariantReports('IossifovWE2014')
        self.assertFalse(vr.families_report)
        self.assertFalse(vr.denovo_report)

        vr.build()
        self.assertTrue(vr.families_report)
        self.assertTrue(vr.denovo_report)

    def test_children_counters_we_studies(self):
        fr = FamiliesReport('TEST WHOLE EXOME')
        fr.build()
        cc = fr.get_children_counters('unaffected')
        self.assertEquals(1463, cc.children_male)
        self.assertEquals(1567, cc.children_female)

    def test_children_counters_lifton_studies(self):
        fr = FamiliesReport('Lifton2013CHD')
        fr.build()
        cc = fr.get_children_counters('unaffected')
        self.assertEquals(133, cc.children_male)
        self.assertEquals(131, cc.children_female)
