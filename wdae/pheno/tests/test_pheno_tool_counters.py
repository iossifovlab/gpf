'''
Created on Aug 9, 2016

@author: lubo
'''
import unittest
from pheno import pheno_request, pheno_tool


class Test(unittest.TestCase):

    def test_pheno_with_family_pheno_filter(self):
        data = {
            'phenoMeasure': 'head_circumference',
            'familyPhenoMeasure': 'non_verbal_iq',
            'familyPhenoMeasureMin': 0,
            'familyPhenoMeasureMax': 40,
            'effectTypeGroups': 'LGDs',
            'presentInParent': 'neither',
        }
        req = pheno_request.Request(data)
        tool = pheno_tool.PhenoTool(req)

        [male, female] = tool.calc()
        counters = tool.counters()

        self.assertEquals(
            counters['autism']['male'],
            male['positiveCount'] + male['negativeCount']
        )

        self.assertEquals(
            counters['autism']['female'],
            female['positiveCount'] + female['negativeCount']
        )


class CountersTest(unittest.TestCase):
    DATA = [
        {
            u'phenoMeasure': u'non_verbal_iq',
            u'denovoStudies': u'ALL SSC',
            u'effectTypeGroups': u'LGDs',
            u'presentInParent': u'neither',
        },
        {
            u'phenoMeasure': u'head_circumference',
            u'denovoStudies': u'ALL SSC',
            u'effectTypeGroups': u'LGDs',
            u'presentInParent': u'neither',
        }
    ]

    def test(self):
        for data in self.DATA:
            req = pheno_request.Request(data)
            tool = pheno_tool.PhenoTool(req)

            [male, female] = tool.calc()
            counters = tool.counters()

            self.assertEquals(
                counters['autism']['male'],
                male['positiveCount'] + male['negativeCount']
            )

            self.assertEquals(
                counters['autism']['female'],
                female['positiveCount'] + female['negativeCount']
            )
