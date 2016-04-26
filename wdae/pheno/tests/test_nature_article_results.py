'''
Created on Nov 24, 2015

@author: lubo
'''
import os
import unittest
import pandas as pd
import numpy as np
from pheno.report import pheno_calc, EFFECT_TYPE_GROUPS


def prepare_pheno_data(df):
    yield tuple(['family_id', 'gender', 'LGDs', 'missense',
                 'synonymous', 'CNV', 'non_verbal_iq', 'age',
                 'non_verbal_iq', 'non_verbal_iq'])

    for _index, row in df.iterrows():
        yield tuple([row['familyId'],
                     row['probandGender'],
                     row['LGDs'],
                     row['missense'],
                     row['synonymous'],
                     0,
                     row['nvIQ'],
                     row['evalAgeInMonths'],
                     row['nvIQ'],
                     row['nvIQ'],
                     ])


class Test(unittest.TestCase):
    FILENAME = os.path.join(os.path.dirname(__file__), "phnGnt.csv")

    def setUp(self):
        self.df = pd.read_csv(self.FILENAME,
                              sep='\t')
        # self.df.dropna(inplace=True)
        self.df = self.df[~np.isnan(self.df.nvIQ.values)]

        self.df.probandGender.replace('male', 'M', inplace=True)
        self.df.probandGender.replace('female', 'F', inplace=True)

    def tearDown(self):
        pass

    def test_df_not_none(self):
        self.assertIsNotNone(self.df)

    def test_df_available_columns(self):
        self.assertIn('nvIQ', self.df.columns)
        self.assertIn('vIQ', self.df.columns)
        self.assertIn('evalAgeInMonths', self.df.columns)
        self.assertIn('familyId', self.df.columns)
        self.assertIn('probandGender', self.df.columns)

    def test_df_gender_and_fix(self):
        gender = np.unique(self.df.probandGender.values)
        self.assertEqual(2, len(gender))
        self.assertEqual('F', gender[0])
        self.assertEqual('M', gender[1])

    def test_df_non_verbal_iq_nans(self):
        nans = self.df[np.isnan(self.df.nvIQ.values)]
        self.assertEqual(0, len(nans))

#     @staticmethod
#     def fix_nan(val):
#         if np.isnan(val):
#             return 0
#         else:
#             return val

    @staticmethod
    def get_pvalue(effect, gender, ph):
        for p in ph:
            if p[0] == effect and p[1] == gender:
                return p[6]

    def test_prepare_pheno_data(self):
        ps = prepare_pheno_data(self.df)
        for c, _r in enumerate(ps):
            pass
        self.assertEqual(2757, c)

    def test_pheno_calc(self):
        ps = prepare_pheno_data(self.df)
        result = pheno_calc(ps, EFFECT_TYPE_GROUPS)
        self.assertIsNotNone(result)
        # self.assertEqual('0.00001', self.get_pvalue('recLGDs', 'M', result))
        # self.assertEqual('0.04', self.get_pvalue('recLGDs', 'F', result))

        # self.assertEqual('0.00002', self.get_pvalue('recLGDs', 'M', result))
        # self.assertEqual('0.05', self.get_pvalue('recLGDs', 'F', result))

        self.assertEqual('0.004', self.get_pvalue('LGDs', 'M', result))
        self.assertEqual('0.4', self.get_pvalue('LGDs', 'F', result))

        # self.assertEqual('0.01', self.get_pvalue('LGDs', 'M', result))
        # self.assertEqual('0.4', self.get_pvalue('LGDs', 'F', result))

        self.assertEqual('0.9', self.get_pvalue('missense', 'M', result))
        self.assertEqual('0.7', self.get_pvalue('missense', 'F', result))

        # self.assertEqual('0.9', self.get_pvalue('missense', 'M', result))
        # self.assertEqual('0.8', self.get_pvalue('missense', 'F', result))

        self.assertEqual('0.4', self.get_pvalue('synonymous', 'M', result))
        self.assertEqual('0.2', self.get_pvalue('synonymous', 'F', result))

        # self.assertEqual('0.4', self.get_pvalue('synonymous', 'M', result))
        # self.assertEqual('0.3', self.get_pvalue('synonymous', 'F', result))


if __name__ == "__main__":
    unittest.main()
