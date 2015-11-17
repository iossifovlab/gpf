'''
Created on Nov 16, 2015

@author: lubo
'''
import unittest
from pheno.report import family_pheno_query_variants


class Test(unittest.TestCase):

    def test_family_pheno_query_variants(self):
        data = {
            'denovoStudies': 'ALL SSC',
        }
        res = family_pheno_query_variants(data)
        self.assertIn('LGDs', res)
        self.assertIn('LGDs.Rec', res)
        self.assertIn('missense', res)
        self.assertIn('synonymous', res)
        self.assertIn('CNV+,CNV-', res)
        self.assertEqual(5, len(res.keys()))

#     def test_prepare_families_gender_data(self):
#         data = {
#             'denovoStudies': 'ALL SSC',
#             'phenoMeasure': 'head_circumference',
#         }
#         res = prepare_families_gender_data(data)
#         self.assertIsNotNone(res)

if __name__ == "__main__":
    unittest.main()
