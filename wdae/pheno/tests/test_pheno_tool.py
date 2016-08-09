'''
Created on Aug 9, 2016

@author: lubo
'''
import unittest
from pheno import pheno_request, pheno_tool


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass()
        cls.data = {
            u'phenoMeasure': u'head_circumference',
            u'normalizedBy': u'normByAge',
            u'denovoStudies': u'ALL SSC',
            u'effectTypeGroups': u'LGDs',
            u'presentInParent': u'neither',
        }
        cls.req = pheno_request.Request(cls.data)
        cls.tool = pheno_tool.PhenoTool(cls.req)

    def test_non_verbal_iq_lgds(self):
        self.assertIsNotNone(self.req)
        self.assertIsNotNone(self.tool)

        families_with_variants = self.tool._build_families_variants()
        self.assertIsNotNone(families_with_variants)

        for fid in families_with_variants['LGDs'].keys():
            self.assertIn(fid, self.req.families)

    def test_table_header(self):
        gen = self.tool.build_data_table()
        header = gen.next()

        self.assertEquals(8, len(header))
        self.assertIn('family_id', header)
        self.assertIn('person_id', header)
        self.assertIn('gender', header)
        self.assertIn('LGDs', header)
        self.assertIn('head_circumference', header)
        self.assertIn('non_verbal_iq', header)
        self.assertIn('age', header)
        self.assertIn('head_circumference ~ age', header)

    def test_table_first_row(self):
        gen = self.tool.build_data_table()
        gen.next()

        row = gen.next()
        self.assertEquals(8, len(row))

    def test_data_array(self):
        data = self.tool._build_data_array()
        self.assertIsNotNone(data)

    def test_calc(self):
        result = self.tool.calc()
        print(result)
        self.assertIsNotNone(result)

    def test_counts(self):
        result = self.tool.calc()
        [male, female] = result

        counters = self.tool.counters()
        print(counters)
        print(male)
        print(female)

        self.assertEquals(
            counters['autism']['male'],
            male['positiveCount'] + male['negativeCount']
        )

        self.assertEquals(
            counters['autism']['female'],
            female['positiveCount'] + female['negativeCount']
        )
