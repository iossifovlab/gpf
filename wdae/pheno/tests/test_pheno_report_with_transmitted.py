'''
Created on Apr 15, 2016

@author: lubo
'''
import unittest

from pheno.report import family_pheno_query_variants, \
    DEFAULT_EFFECT_TYPE_GROUPS
from DAE import vDB


class Test(unittest.TestCase):

    def test_single_gene_sym(self):
        data = {
            'denovoStudies': 'ALL SSC',
            'transmittedStudies': 'w1202s766e611',
            'presentInParent': "father only",
            'geneSyms': "POGZ",

        }
        res = family_pheno_query_variants(data, DEFAULT_EFFECT_TYPE_GROUPS)

        self.assertIn('LGDs', res)
        self.assertIn('missense', res)
        self.assertIn('synonymous', res)
        self.assertIn('CNV+,CNV-', res)
        self.assertEqual(4, len(res.keys()))
        self.assertEqual(0, len(res['LGDs']))
        self.assertEqual(42, len(res['missense']))
        self.assertEqual(119, len(res['synonymous']))
        self.assertEqual(0, len(res['CNV+,CNV-']))

    def test_gene_set(self):
        data = {
            'denovoStudies': 'ALL SSC',
            'transmittedStudies': 'w1202s766e611',
            'presentInParent': "father only",
            # 'geneSyms': "POGZ",
            'geneSet': "main",
            'geneTerm': "ChromatinModifiers",

        }
        res = family_pheno_query_variants(data, DEFAULT_EFFECT_TYPE_GROUPS)
        self.assertIn('LGDs', res)
        self.assertIn('missense', res)
        self.assertIn('synonymous', res)
        self.assertIn('CNV+,CNV-', res)
        self.assertEqual(4, len(res.keys()))
        self.assertEqual(268, len(res['LGDs']))
        self.assertEqual(2462, len(res['missense']))
        self.assertEqual(2462, len(res['synonymous']))
        self.assertEqual(0, len(res['CNV+,CNV-']))

    def test_experiment_with_mysql_families_with_variants(self):
        query = {
            'minParentsCalled': 0,
            'minAltFreqPrcnt': -1.0,
            'familyIds': None,
            'gender': None,
            'geneSyms': set(['POGZ']),
            'ultraRareOnly': False,
            'regionS': None,
            'effectTypes': ['missense'],
            'inChild': 'prb',
            'limit': None,
            'variantTypes': None,
            'presentInParent': ['father only'],
            'TMM_ALL': False,
            'presentInChild': None,
            'maxAltFreqPrcnt': 100.0}
        st = vDB.get_study('w1202s766e611')

        fit = st.get_families_with_transmitted_variants(**query)
        families = [f for f in fit]
        self.assertEquals(42, len(families))

    def test_experiment_with_mysql_families_with_variants_all(self):
        query = {
            'minParentsCalled': 0,
            'minAltFreqPrcnt': -1.0,
            'familyIds': None,
            'gender': None,
            'ultraRareOnly': False,
            'regionS': None,
            'effectTypes': ["no-frame-shift-newStop",
                            "frame-shift", "nonsense", "splice-site"],
            'inChild': 'prb',
            'limit': None,
            'variantTypes': None,
            'presentInParent': ['father only'],
            'TMM_ALL': False,
            'presentInChild': None,
            'maxAltFreqPrcnt': 100.0}
        st = vDB.get_study('w1202s766e611')

        fit = st.get_families_with_transmitted_variants(**query)
        families = [f for f in fit]
        self.assertEquals(2462, len(families))

if __name__ == "__main__":
    unittest.main()
